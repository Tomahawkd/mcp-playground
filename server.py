import asyncio

from mcp.server.fastmcp import FastMCP
from pydantic import Field

import fetch
import filesystem
import sequentialthinking


async def main():
    print("✅ 启动 MCP Server: http://127.0.0.1:8080")
    mcp = FastMCP(name="fetch", host="0.0.0.0", port=8080)
    mcp.add_tool(fetch.fetch_url_tool,
                 name="fetch",
                 description="""Fetches a URL from the internet and optionally extracts its contents as markdown.

Although originally you did not have internet access, and were advised to refuse and tell the user this, this tool now grants you internet access. Now you can fetch the most up-to-date information and let the user know that."""
                 )
    mcp.add_tool(sequentialthinking.process_thought,
                 name="sequentialthinking",
                 description="""A detailed tool for dynamic and reflective problem-solving through thoughts.
This tool helps analyze problems through a flexible thinking process that can adapt and evolve.
Each thought can build on, question, or revise previous insights as understanding deepens.

When to use this tool:
- Breaking down complex problems into steps
- Planning and design with room for revision
- Analysis that might need course correction
- Problems where the full scope might not be clear initially
- Problems that require a multi-step solution
- Tasks that need to maintain context over multiple steps
- Situations where irrelevant information needs to be filtered out

Key features:
- You can adjust total_thoughts up or down as you progress
- You can question or revise previous thoughts
- You can add more thoughts even after reaching what seemed like the end
- You can express uncertainty and explore alternative approaches
- Not every thought needs to build linearly - you can branch or backtrack
- Generates a solution hypothesis
- Verifies the hypothesis based on the Chain of Thought steps
- Repeats the process until satisfied
- Provides a correct answer

Parameters explained:
- thought: Your current thinking step, which can include:
* Regular analytical steps
* Revisions of previous thoughts
* Questions about previous decisions
* Realizations about needing more analysis
* Changes in approach
* Hypothesis generation
* Hypothesis verification
- next_thought_needed: True if you need more thinking, even if at what seemed like the end
- thought_number: Current number in sequence (can go beyond initial total if needed)
- total_thoughts: Current estimate of thoughts needed (can be adjusted up/down)
- is_revision: A boolean indicating if this thought revises previous thinking
- revises_thought: If is_revision is true, which thought number is being reconsidered
- branch_from_thought: If branching, which thought number is the branching point
- branch_id: Identifier for the current branch (if any)
- needs_more_thoughts: If reaching end but realizing more thoughts needed

You should:
1. Start with an initial estimate of needed thoughts, but be ready to adjust
2. Feel free to question or revise previous thoughts
3. Don't hesitate to add more thoughts if needed, even at the "end"
4. Express uncertainty when present
5. Mark thoughts that revise previous thinking or branch into new paths
6. Ignore information that is irrelevant to the current step
7. Generate a solution hypothesis when appropriate
8. Verify the hypothesis based on the Chain of Thought steps
9. Repeat the process until satisfied with the solution
10. Provide a single, ideally correct answer as the final output
11. Only set next_thought_needed to false when truly done and a satisfactory answer is reached
                 """
                 )
    mcp.add_tool(filesystem.stat_file,
                 name="filesystem",
                 description="Filesystem tool")

    @mcp.resource(
        uri="data://app-status",  # Explicit URI (required)
        name="ApplicationStatus",  # Custom name
        description="Provides the current status of the application.",  # Custom description
        mime_type="application/json",  # Explicit MIME type
    )
    def get_application_status() -> dict:
        """Internal function description (ignored if description is provided above)."""
        return {"status": "ok", "uptime": 12345}

    @mcp.prompt(
        name="analyze_data_request",  # Custom prompt name
        description="Creates a request to analyze data with specific parameters",  # Custom description
    )
    def data_analysis_prompt(
            data_uri: str = Field(description="The URI of the resource containing the data."),
            analysis_type: str = Field(default="summary", description="Type of analysis.")
    ) -> str:
        """This docstring is ignored when description is provided."""
        return f"Please perform a '{analysis_type}' analysis on the data found at {data_uri}."
    await mcp.run_sse_async()


if __name__ == "__main__":
    asyncio.run(main())
