# MCP File Reader

A minimal **Model Context Protocol (MCP)** project demonstrating AI + tool calling.

- **MCP server** (`mcp_server.py`) exposes one tool: `read_file(path)`.
- **MCP client** (`mcp_client.py`) launches the server over stdio and discovers/invokes its tools.
- **AI messenger** (`ai_messenger.py`) wires those tools to a **Groq** LLM and runs the chat-with-tools loop.
- **CLI** (`cli.py`) lets you chat in the terminal. When you ask about a file, the AI calls `read_file` and answers from the real contents.

## How it works

```
you (terminal) → CLI → AIMessenger → Groq LLM
                            │             │
                            │      "call read_file"
                            ▼             ▼
                        MCPClient → MCP server runs read_file → contents fed back to LLM → answer
```

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10+.

```bash
uv sync                       # install dependencies
```

Then create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_key_here
GROQ_LLM_MODEL=llama-3.3-70b-versatile
```

Get a free Groq API key at https://console.groq.com/keys.

## Run

```bash
uv run mcp-chat
# or:
uv run python cli.py
```

Then try:

```
you> What does README.md contain?
you> Summarize the file ./mcp_server.py
```

Type `exit` or `quit` to leave.

## Files

| File | Role |
|------|------|
| `mcp_server.py` | MCP server with the `read_file` tool (stdio transport) |
| `mcp_client.py` | MCP client: launches the server, discovers and calls its tools |
| `ai_messenger.py` | Groq chat-with-tools loop, driving the MCP client |
| `cli.py` | Terminal REPL |

The model is configured via the `GROQ_LLM_MODEL` environment variable (e.g. `llama-3.3-70b-versatile`).
