import asyncio
from typing import Tuple, Dict

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

import fetch
import filesystem
import sequentialthinking


class CustomMCPClient:
    def __init__(self, server_url="http://127.0.0.1:8080/sse"):
        self.server_url = server_url
        self._sse_context = None
        self._session: ClientSession = None

    async def __aenter__(self):
        # 创建 SSE 通道
        self._sse_context = sse_client(self.server_url)
        self.read, self.write = await self._sse_context.__aenter__()

        # 创建 MCP 会话
        self._session = ClientSession(self.read, self.write)
        await self._session.__aenter__()
        await self._session.initialize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
        if self._sse_context:
            await self._sse_context.__aexit__(exc_type, exc_val, exc_tb)

    async def list_tools(self):
        return await self._session.list_tools()

    async def call_tool(self, args: Tuple[str, Dict[str, str]]):
        return await self._session.call_tool(args[0], args[1])

    async def list_resources(self):
        return await self._session.list_resources()

    async def get_resource(self, url):
        return await self._session.read_resource(url)

    async def list_prompts(self):
        return await self._session.list_prompts()

    async def get_prompt(self, args: Tuple[str, Dict[str, str]]):
        return await self._session.get_prompt(args[0], args[1])


async def main():
    async with CustomMCPClient() as client:
        print("✅ 成功连接 MCP Server")
        tools = await client.list_tools()

        print("\n🛠 可用工具:")
        print(tools)

        resources = await client.list_resources()
        print("\n📚 可用资源:")
        print(resources)

        p = await client.list_prompts()
        print("\n📚 可用Prompt:")
        print(p)

        tools = {
            "fetch": fetch.send_request,
            "sequentialthinking": sequentialthinking.send_request,
            "filesystem": filesystem.send_request
        }

        for tool, func in tools.items():
            print(f"\n📡 调用工具: {tool}")
            result = await client.call_tool(func())

            print("\n🎯 工具返回:")
            for item in result.content:
                print(" -", item.text)

        res = [
            "data://app-status"
        ]

        for r in res:
            print(f"\n📡 获取资源: {r}")
            result = await client.get_resource(r)

            print("\n🎯 资源返回:")
            for item in result.contents:
                print(" -", item.text)

        prompt = {
            "analyze_data_request": {"data_uri": "123", "analysis_type": "type"}
        }

        for k,v in prompt.items():
            print(f"\n📡 获取Prompt: {k}")
            result = await client.get_prompt((k,v))

            print("\n🎯 Prompt返回:")
            for item in result.messages:
                print(" -", item)


if __name__ == "__main__":
    asyncio.run(main())