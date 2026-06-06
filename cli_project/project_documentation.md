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
MCPChat (core/mcp_chat.py)  →  a specialized version of Chat
   │  (extends ↓)
Chat (core/chat.py)  →  runs the conversation loop  ← THIS FILE
   │
   ├── Messenger     → talks to the Groq AI
   ├── Conversation  → holds the conversation history
   └── ToolManager + MCPClients → runs tools the AI requests
```

So `chat.py` is the **orchestration layer**. It doesn't talk to the AI directly, it doesn't store the history itself, and it doesn't run tools directly — it **coordinates** those helpers in the right order to turn your question into a final answer.

One note: in `main.py`, the app actually uses `MCPChat` (in `core/mcp_chat.py`), which is a more specialized child of this `Chat` class. So `Chat` here is the **base/foundation** that handles the core conversation loop, and `MCPChat` builds extra command-line features on top of it.

---

## `core/mcp_chat.py`

### What `mcp_chat.py` is

`mcp_chat.py` defines one class called **`MCPChat`**. It is a **document-aware version of `Chat`** — it takes the basic conversation engine from `chat.py` and adds the smarts to handle documents.

The key idea is **inheritance**: `MCPChat` *extends* `Chat` (written as `class MCPChat(Chat)`). That means it automatically gets everything `Chat` can do (the `run` loop, the conversation history, talking to the AI), and only adds the *new* parts on top. It doesn't repeat the conversation logic — it reuses it.

What does it add? Two abilities, both triggered by what the user types:

| You type... | `MCPChat` does... |
|---|---|
| `@report.docx` | Fetches that document's text and slips it into the prompt as context |
| `/summarize report.docx` | Loads a ready-made prompt template from the server and runs it |

To do this it talks to a special **"doc server"** over MCP (the `doc_client`), which stores the documents and prompt templates.

> 💡 **Why the name "MCP"?** MCP (Model Context Protocol) is a standard way for an app to connect to outside "servers" that give the AI extra abilities. Here, one MCP server (`mcp_server.py`) holds the documents. `MCPChat` is the chat class that knows how to ask that server for things.

### Walking through the code

#### The setup (`__init__`)
```python
def __init__(self, doc_client, clients, messenger):
    super().__init__(messenger=messenger, clients=clients)  # let Chat set itself up
    self.doc_client = doc_client                            # remember the document server
```
`super().__init__(...)` is the line that says *"run the parent `Chat`'s setup first"* — that's what creates the conversation history and stores the messenger. Then `MCPChat` saves one extra thing: `doc_client`, the connection it uses to fetch documents and prompts.

#### The little "ask the server" helpers
These four short methods are simple wrappers around the doc server. Each one asks the server for one specific thing:

| Method | What it fetches |
|---|---|
| `list_prompts()` | The available `/commands` (prompt templates) |
| `list_docs_ids()` | The names of all known documents |
| `get_doc_content(doc_id)` | The full text of one document |
| `get_prompt(command, doc_id)` | A filled-in prompt template for a command |

#### Handling `@mentions` (`_extract_resources`)
```python
mentions = [word[1:] for word in query.split() if word.startswith("@")]
```
This scans your message for any word starting with `@`, and chops off the `@`. So `"summarize @report.docx"` gives `["report.docx"]`. It then fetches each mentioned document that actually exists and wraps them in `<document>` tags, returning one big string of context for the AI to read.

#### Handling `/commands` (`_process_command`)
If your message is a command like `/summarize report.docx`, this method splits it into the command name (`summarize`) and the document id (`report.docx`), asks the server to build the matching prompt, and adds it straight to the conversation.

> ⚠️ **Known gotcha:** it reads `words[1]` for the document id, so typing a command with no document (just `/summarize`) would cause an error. Worth a guard if commands-without-arguments should be allowed.

#### The decision point (`_process_query`) — the heart of this file
This method **overrides** the simpler `_process_query` from `Chat`. It runs for every message and decides what kind of message it is:

```python
async def _process_query(self, query):
    if query.startswith("/"):          # a command?
        await self._process_command(query)
        return

    added_resources = await self._extract_resources(query)   # any @docs?
    prompt = f"""...{query}...{added_resources}..."""        # wrap question + context
    self.conversation.add_user_message(prompt)
```

In plain English:
1. **Is it a `/command`?** → handle it and stop.
2. **Otherwise** → gather any `@mentioned` documents, wrap your question together with that document context plus instructions, and add the whole thing to the conversation.

After this runs, the inherited `Chat.run` loop takes over and talks to the AI as usual.

#### The format converters (`_get_field`, `convert_prompt_message_to_message_param`, …)
The doc server returns prompt messages in **MCP's format**, but the AI model expects plain dictionaries like `{"role": "user", "content": "..."}`. These bottom functions are **translators**:

- `_get_field(item, key)` — reads a field whether the data is a dictionary (`.get()`) or a custom object (`getattr()`). It's the one place that knows about that difference.
- `convert_prompt_message_to_message_param(...)` — converts **one** message into the AI's format (handling single-text, a list of text blocks, or nothing usable).
- `convert_prompt_messages_to_message_params(...)` — runs the above on a **whole list** of messages.

### Its role in the project

Looking back at the app's flow:

```
main.py  →  creates MCPChat and hands it the doc server
   │
   ↓
CliApp (core/cli.py)  →  reads what you type in the terminal
   │
   ↓
MCPChat (core/mcp_chat.py)  →  resolves @docs and /commands  ← THIS FILE
   │  (extends ↓)
Chat (core/chat.py)  →  runs the conversation loop with the AI
```

So `mcp_chat.py` is the **document/command layer**. It sits between the terminal interface and the base conversation engine: it enriches your message with documents (or expands it from a command template) *before* handing it down to `Chat`, which does the actual back-and-forth with the AI. `cli.py` handles the terminal, `chat.py` handles the AI loop, and `mcp_chat.py` is the bridge that makes the chat document-aware.
