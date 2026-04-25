# CLI-Chatbot

A terminal-based AI research agent powered by **Claude** (Anthropic). It runs fully in the CLI with a rich, colored interface — showing tool calls, file operations, and web searches live as they happen.

## Features

- **Web Search** — searches the internet using Claude's built-in web search tool (up to 3 searches per query)
- **File Reading** — reads local `.txt` / `.md` files on demand
- **File Writing** — saves research reports and outputs directly to disk
- **Live Tool Display** — every tool call and result is shown inline in real time using `rich`
- **Multi-turn Conversation** — context is preserved across messages in the same session
- **Session Logging** — every message, tool call, and response is appended to `chat_log.jsonl`

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

## Installation

```bash
# Clone the repo
git clone https://github.com/chanakyagt/CLI-Chatbot.git
cd CLI-Chatbot

# Create and activate a virtual environment
python -m venv myenv
myenv\Scripts\activate        # Windows
# source myenv/bin/activate   # macOS/Linux

# Install dependencies
pip install anthropic python-dotenv rich
```

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

```bash
python chatbot.py
```

Type your research task and press **Enter**. The agent will search the web, create files, and show its progress live.

```
You: Research the top 5 use cases of vertical farming and save a report to farming_report.md
```

Type `quit`, `exit`, or `q` to stop. Press `Ctrl+C` to force quit.

## How It Works

```
User message
     │
     ▼
Claude (claude-sonnet-4-5)
     │
     ├── 🌐 web_search  → searches the internet
     ├── 📖 read_file   → reads a local file
     └── 📝 write_file  → saves output to disk
     │
     ▼
Agent loop continues until end_turn or max_tokens
```

## Log File

Each session appends structured entries to `chat_log.jsonl`:

```jsonl
{"timestamp": "...", "session_id": "a1b2c3d4", "type": "session_start"}
{"timestamp": "...", "session_id": "a1b2c3d4", "type": "user_message", "content": "..."}
{"timestamp": "...", "session_id": "a1b2c3d4", "type": "tool_call", "tool": "web_search", "input": {...}}
{"timestamp": "...", "session_id": "a1b2c3d4", "type": "tool_result", "tool": "web_search", "success": true, "content": "..."}
{"timestamp": "...", "session_id": "a1b2c3d4", "type": "agent_response", "content": "..."}
{"timestamp": "...", "session_id": "a1b2c3d4", "type": "session_end"}
```

Each session gets a unique 8-character ID shown at startup.

## Project Structure

```
CLI-Chatbot/
├── chatbot.py       # Main chatbot script
├── main.ipynb       # Original notebook (reference)
├── main.py          # Standalone script version
├── chat_log.jsonl   # Auto-generated session log
├── .env             # API key (not committed)
└── README.md
```

## License

MIT
