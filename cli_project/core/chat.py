from core.messenger import Messenger
from core.conversation import Conversation
from mcp_client import MCPClient
from core.tools import ToolManager


# The "brain" / conductor of the app: runs the back-and-forth conversation
# between the user, the AI model, and the tools the AI can use.
class Chat:
  def __init__(self, messenger: Messenger, clients: dict[str, MCPClient]):
    # Talks to the actual AI model (sends messages, gets replies).
    self.messenger: Messenger = messenger
    # The tool servers the AI can use, keyed by a name (e.g. "doc_client").
    self.clients: dict[str, MCPClient] = clients
    # Owns the conversation history / memory and all logic for adding to it.
    self.conversation: Conversation = Conversation()

  async def _process_query(self, query: str):
    # Add whatever the user typed to the history, tagged as the "user" role.
    self.conversation.add_user_message(query)

  async def run(
      self,
      query: str,
  ) -> str:
    final_text_response = ""

    # 1. Add the user's question to the conversation history.
    await self._process_query(query)

    # 2. Keep looping until the AI gives a final answer. The AI may first ask
    #    to run one or more tools before it can respond.
    while True:
      # 3. Send the full conversation (plus the list of available tools) to
      #    the AI and get its response.
      response = self.messenger.chat(
          messages=self.conversation.messages(),
          tools=await ToolManager.get_all_tools(self.clients),
      )

      # 4. Save the AI's reply (including any tool calls it requested) to history.
      self.conversation.add_assistant_message(response)

      # 5a. The AI wants to use a tool first instead of answering directly.
      if response.choices[0].finish_reason == "tool_calls":
        print(self.messenger.text_from_message(response))
        # Run the requested tool(s)...
        tool_result_parts = await ToolManager.execute_tool_requests(
            self.clients, response
        )

        # ...feed the results back into the history, then loop again so the
        # AI can continue now that it has the info it needed.
        self.conversation.add_tool_results(tool_result_parts)
      else:
        # 5b. The AI gave a normal text answer, so grab it and stop the loop.
        final_text_response = self.messenger.text_from_message(
            response
        )
        self.conversation.clear()  # Clear conversation history after getting the final response
        break

    # 6. Return the AI's final answer.
    return final_text_response
