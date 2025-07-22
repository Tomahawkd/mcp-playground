from typing import Annotated, Tuple
from urllib.parse import urlparse, urlunparse

import markdownify
import readabilipy.simple_json
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import (
    ErrorData,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)
from protego import Protego
from pydantic import Field, AnyUrl

DEFAULT_USER_AGENT_AUTONOMOUS = "ModelContextProtocol/1.0 (Autonomous; +https://github.com/modelcontextprotocol/servers)"

user_agent_autonomous: str = DEFAULT_USER_AGENT_AUTONOMOUS
ignore_robots_txt: bool = False
proxy_url: str | None = None

mcp = FastMCP(name="fetch", host="0.0.0.0", port=8080)


def extract_content_from_html(html: str) -> str:
    """Extract and convert HTML content to Markdown format.

    Args:
        html: Raw HTML content to process

    Returns:
        Simplified markdown version of the content
    """
    ret = readabilipy.simple_json.simple_json_from_html_string(
        html, use_readability=True
    )
    if not ret["content"]:
        return "<error>Page failed to be simplified from HTML</error>"
    content = markdownify.markdownify(
        ret["content"],
        heading_style=markdownify.ATX,
    )
    return content


def get_robots_txt_url(url: str) -> str:
    """Get the robots.txt URL for a given website URL.

    Args:
        url: Website URL to get robots.txt for

    Returns:
        URL of the robots.txt file
    """
    # Parse the URL into components
    parsed = urlparse(url)

    # Reconstruct the base URL with just scheme, netloc, and /robots.txt path
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))

    return robots_url


async def check_may_autonomously_fetch_url(url: str, user_agent: str, proxy_url: str | None = None) -> None:
    """
    Check if the URL can be fetched by the user agent according to the robots.txt file.
    Raises a McpError if not.
    """
    from httpx import AsyncClient, HTTPError

    robot_txt_url = get_robots_txt_url(url)

    async with AsyncClient(proxy=proxy_url) as client:
        try:
            response = await client.get(
                robot_txt_url,
                follow_redirects=True,
                headers={"User-Agent": user_agent},
            )
        except HTTPError:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"Failed to fetch robots.txt {robot_txt_url} due to a connection issue",
            ))
        if response.status_code in (401, 403):
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"When fetching robots.txt ({robot_txt_url}), received status {response.status_code} so assuming that autonomous fetching is not allowed, the user can try manually fetching by using the fetch prompt",
            ))
        elif 400 <= response.status_code < 500:
            return
        robot_txt = response.text
    processed_robot_txt = "\n".join(
        line for line in robot_txt.splitlines() if not line.strip().startswith("#")
    )
    robot_parser = Protego.parse(processed_robot_txt)
    if not robot_parser.can_fetch(str(url), user_agent):
        raise McpError(ErrorData(
            code=INTERNAL_ERROR,
            message=f"The sites robots.txt ({robot_txt_url}), specifies that autonomous fetching of this page is not allowed, "
                    f"<useragent>{user_agent}</useragent>\n"
                    f"<url>{url}</url>"
                    f"<robots>\n{robot_txt}\n</robots>\n"
                    f"The assistant must let the user know that it failed to view the page. The assistant may provide further guidance based on the above information.\n"
                    f"The assistant can tell the user that they can try manually fetching the page by using the fetch prompt within their UI.",
        ))


async def fetch_url(
        url: str, user_agent: str, force_raw: bool = False, proxy_url: str | None = None
) -> Tuple[str, str]:
    """
    Fetch the URL and return the content in a form ready for the LLM, as well as a prefix string with status information.
    """
    from httpx import AsyncClient, HTTPError

    async with AsyncClient(proxy=proxy_url) as client:
        try:
            response = await client.get(
                url,
                follow_redirects=True,
                headers={"User-Agent": user_agent},
                timeout=30,
            )
        except HTTPError as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url}: {e!r}"))
        if response.status_code >= 400:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"Failed to fetch {url} - status code {response.status_code}",
            ))

        page_raw = response.text

    content_type = response.headers.get("content-type", "")
    is_page_html = (
            "<html" in page_raw[:100] or "text/html" in content_type or not content_type
    )

    if is_page_html and not force_raw:
        return extract_content_from_html(page_raw), ""

    return (
        page_raw,
        f"Content type {content_type} cannot be simplified to markdown, but here is the raw content:\n",
    )


async def fetch_url_tool(
        url: Annotated[AnyUrl, Field(description="URL to fetch")],
        max_length: Annotated[
            int, Field(default=5000, description="Maximum number of characters to return.", gt=0, lt=1000000)],
        start_index: Annotated[int, Field(default=0,
                                          description="On return output starting at this character index, useful if a previous fetch was truncated and more context is required.",
                                          ge=0)],
        raw: Annotated[bool, Field(default=False,
                                   description="Get the actual HTML content of the requested page, without simplification.")]
) -> list[str]:
    url = str(url)
    if not url:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="URL is required"))
    if not ignore_robots_txt:
        await check_may_autonomously_fetch_url(url, user_agent_autonomous, proxy_url)
    content, prefix = await fetch_url(
        url, user_agent_autonomous, force_raw=raw, proxy_url=proxy_url
    )
    original_length = len(content)
    if start_index >= original_length:
        content = "<error>No more content available.</error>"
    else:
        truncated_content = content[start_index: start_index + max_length]
        if not truncated_content:
            content = "<error>No more content available.</error>"
        else:
            content = truncated_content
            actual_content_length = len(truncated_content)
            remaining_content = original_length - (start_index + actual_content_length)
            # Only add the prompt to continue fetching if there is still remaining content
            if actual_content_length == max_length and remaining_content > 0:
                next_start = start_index + actual_content_length
                content += f"\n\n<error>Content truncated. Call the fetch tool with a start_index of {next_start} to get more content.</error>"
    return [f"{prefix}Contents of {url}:\n{content}"]

def send_request():
    return "fetch", {"url": "https://github.tomahawkd.online/blogs/20250629-brokenarrow"}