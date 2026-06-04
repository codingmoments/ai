# Project Documentation

## `core/chat.py`

### What `chat.py` is

`chat.py` defines one class called **`Chat`**. Think of it as the **"brain" or conductor** of the whole application. It's the piece that runs the back-and-forth conversation between *you*, the *AI model*, and the *tools* the AI can use.

It's a small file, but it ties together four other parts of the project:

| It uses... | Which does... |
|---|---|
| `Messenger` | Talks to the actual AI model (Groq) — sends messages, gets replies |
| `Conversation` | Owns the conversation history and all the logic for adding messages to it |
| `MCPClient` | Connects to "tool servers" that give the AI extra abilities (like reading documents) |
| `ToolManager` | Lists the available tools and runs them when the AI asks |

> 💡 **Design note:** `Chat` does *not* store the message list itself. The history lives in a dedicated `Conversation` object (`core/conversation.py`), which is the **only** place allowed to change it. This keeps each class focused on one job: `Messenger` talks to Groq, `Conversation` holds the history, and `Chat` just coordinates them.

### Walking through the code

#### The setup (`__init__`)
```python
def __init__(self, messenger: Messenger, clients: dict[str, MCPClient]):
    self.messenger = messenger          # the thing that talks to the AI
    self.clients = clients              # the tool servers it can use
    self.conversation = Conversation()  # owns the history (starts empty)
```
When a `Chat` is created, it's handed a `messenger` (to reach the AI) and `clients` (the tool servers). It also creates a fresh `Conversation` — this is the **memory of the conversation**. Every question and answer gets added to it so the AI remembers what was said earlier.

> 💡 About `dict[str, MCPClient]`: this just means "`clients` is a dictionary where each entry has a **text name** (like `"doc_client"`) pointing to an **`MCPClient`** object." A dictionary is like a labeled box of items. In `main.py` you can see it being filled: `clients["doc_client"] = doc_client`.

#### Adding your question (`_process_query`)
```python
async def _process_query(self, query: str):
    self.conversation.add_user_message(query)
```
This takes whatever you typed and asks the `Conversation` to add it to the history, tagged as a `"user"` message so the AI knows *you* said it. Notice `Chat` doesn't touch the list directly — it just asks `Conversation` to do it.

#### The main loop (`run`) — the heart of the file
This is where the real work happens. Here's the idea in plain English:

```python
async def run(self, query: str) -> str:
    await self._process_query(query)   # 1. add your question to history

    while True:                         # 2. keep looping until the AI is done
        response = self.messenger.chat(messages=self.conversation.messages(), ...)  # 3. ask the AI
        self.conversation.add_assistant_message(response)                           # 4. save the AI's reply

        if response ... == "tool_calls":           # 5a. AI wants to use a tool?
            tool_result = ToolManager.execute_tool_requests(...)
            self.conversation.add_tool_results(...) #     run it, feed result back
        else:                                       # 5b. AI gave a final answer?
            final_text_response = ...
            break                                   #     stop the loop

    return final_text_response          # 6. return the final answer
```

The clever part is the **`while True` loop**. The AI doesn't always answer in one shot. Sometimes it says *"I can't answer yet — first run this tool for me"* (e.g. "read this document"). So the loop works like this:

1. Send the conversation to the AI.
2. **If** the AI asks to use a tool → run the tool, add the result to the conversation, and **loop again** (now the AI has the info it needed).
3. **If** the AI gives a normal text answer → grab that text and **stop the loop**.

This repeat-until-done pattern is what lets the AI use tools step by step before giving you a final answer.

### Its role in the project

The flow of the whole app:

```
main.py  →  starts everything, connects tool servers, creates the chat
   │
   ↓
CliApp (core/cli.py)  →  the command-line interface you type into
   │
   ↓
CliChat (core/cli_chat.py)  →  a specialized version of Chat
   │  (extends ↓)
Chat (core/chat.py)  →  runs the conversation loop  ← THIS FILE
   │
   ├── Messenger     → talks to the Groq AI
   ├── Conversation  → holds the conversation history
   └── ToolManager + MCPClients → runs tools the AI requests
```

So `chat.py` is the **orchestration layer**. It doesn't talk to the AI directly, it doesn't store the history itself, and it doesn't run tools directly — it **coordinates** those helpers in the right order to turn your question into a final answer.

One note: in `main.py`, the app actually uses `CliChat` (in `core/cli_chat.py`), which is a more specialized child of this `Chat` class. So `Chat` here is the **base/foundation** that handles the core conversation loop, and `CliChat` builds extra command-line features on top of it.
