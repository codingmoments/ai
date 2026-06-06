import json
from typing import List
from mcp.types import CallToolResult, TextContent
from mcp_client import MCPClient


class ToolManager:
  @staticmethod
  async def get_all_tools(client: MCPClient) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.inputSchema,
            },
        }
        for t in await client.list_tools()
    ]

  @staticmethod
  def _tool_result(tool_call_id: str, content: str) -> dict:
    return {"role": "tool", "tool_call_id": tool_call_id, "content": content}

  @classmethod
  async def execute_tool_requests(cls, client: MCPClient, response) -> List[dict]:
    tool_calls = response.choices[0].message.tool_calls or []
    results: list[dict] = []

    for tc in tool_calls:
      tool_name = tc.function.name
      try:
        output: CallToolResult | None = await client.call_tool(
            tool_name, json.loads(tc.function.arguments)
        )
        items = output.content if output else []
        content = json.dumps(
            [item.text for item in items if isinstance(item, TextContent)]
        )
      except Exception as e:
        content = json.dumps({"error": f"Error executing tool '{tool_name}': {e}"})
        print(content)
      results.append(cls._tool_result(tc.id, content))

    return results
