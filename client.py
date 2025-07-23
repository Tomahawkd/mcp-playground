import asyncio

from fastmcp import Client

import fetch
import filesystem
import sequentialthinking


async def main():
    async with Client("http://127.0.0.1:8080/sse") as client:
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
            name, arg = func()
            result = await client.call_tool(name, arg)

            print("\n🎯 工具返回:")
            for item in result.content:
                print(" -", item.text)

        res = [
            "data://app-status"
        ]

        for r in res:
            print(f"\n📡 获取资源: {r}")
            result = await client.read_resource(r)

            print("\n🎯 资源返回:")
            for item in result:
                print(" -", item.text)

        prompt = {
            "analyze_data_request": {"data_uri": "123", "analysis_type": "type"}
        }

        for k, v in prompt.items():
            print(f"\n📡 获取Prompt: {k}")
            result = await client.get_prompt(k, v)

            print("\n🎯 Prompt返回:")
            for item in result.messages:
                print(" -", item)


if __name__ == "__main__":
    asyncio.run(main())
