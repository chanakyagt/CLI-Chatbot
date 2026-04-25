#!/usr/bin/env python3
"""AI Research Agent - Terminal Chatbot Interface"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
from anthropic.types import ToolUseBlock, TextBlock
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.prompt import Prompt
from rich.rule import Rule

load_dotenv()

LOG_FILE = Path("chat_log.jsonl")

def log(entry_type: str, data: dict, session_id: str):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "type": entry_type,
        **data,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

client = Anthropic()
MODEL = "claude-sonnet-4-5"
console = Console()

SYSTEM = """
You have three tools available: read_file, write_file, and web_search.
- Use web_search ONLY for searching the internet
- Use write_file ONLY for saving files — NEVER use code_execution to write files
- NEVER write files to /tmp/ or any server path
- ALL files must be saved using the write_file tool directly
- Do NOT use code_execution for anything other than what is absolutely necessary
"""

websearch_tool = {"type": "web_search_20260209", "name": "web_search", "max_uses": 3}

read_file_schema = {
    "name": "read_file",
    "description": "Reads the full text content of a local file from disk and returns it as a string. Use this when you need to access information stored in a local .txt or .md file. Only use this for files you know exist on disk. Returns the raw string content of the file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "The name or relative path of the file to read. For example: 'notes.txt' or 'data/report.md'",
            }
        },
        "required": ["file_name"],
    },
}

write_file_schema = {
    "name": "write_file",
    "description": "Writes the given text content to a local file on disk. Use this to save reports, summaries, or any text output. If the file already exists, it will be completely overwritten. Use this as the final step when you are ready to produce the output report.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "The name or relative path of the file to write to. For example: 'report.md' or 'output/summary.txt'",
            },
            "content": {
                "type": "string",
                "description": "The full text content to write into the file.",
            },
        },
        "required": ["file_name", "content"],
    },
}


def read_file(file_name):
    with open(file_name, "r") as f:
        file_content = f.read()
    return f"read_file_status: FILE READ SUCCESSFUL here are the file read contents : {file_content}"


def write_file(file_name, content):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)
    return "write_file_status:FILE WRITE WAS SUCCESSFUL"


tool_lookup = {"read_file": read_file, "write_file": write_file}


def tool_executor(tool_block):
    try:
        tool = tool_lookup[tool_block.name]
        tool_response = tool(**tool_block.input)
        return {
            "type": "tool_result",
            "tool_use_id": tool_block.id,
            "content": tool_response,
            "is_error": False,
        }
    except Exception as e:
        return {
            "type": "tool_result",
            "tool_use_id": tool_block.id,
            "content": f"Error: {e}",
            "is_error": True,
        }


def run_agent(user_message, agent_messages, session_id: str):
    log("user_message", {"content": user_message}, session_id)
    agent_messages = agent_messages + [{"role": "user", "content": user_message}]
    display_text = Text()
    container_id = None

    def make_panel():
        return Panel(
            display_text,
            title="[bold green]🤖 Agent[/bold green]",
            border_style="green",
            padding=(1, 2),
        )

    with Live(make_panel(), console=console, refresh_per_second=10) as live:

        def refresh():
            live.update(make_panel())

        while True:
            params = {
                "messages": agent_messages,
                "model": MODEL,
                "max_tokens": 5000,
                "system": SYSTEM,
                "tools": [read_file_schema, write_file_schema, websearch_tool],
            }
            if container_id:
                params["container"] = container_id

            response = client.messages.create(**params)
            agent_messages = agent_messages + [{"role": "assistant", "content": response.content}]

            if response.container:
                container_id = response.container.id

            if response.stop_reason == "max_tokens":
                display_text.append("\n⚠️  Max tokens reached. Task may be incomplete.", style="bold yellow")
                log("max_tokens", {}, session_id)
                refresh()
                break

            if response.stop_reason == "end_turn":
                final_text = ""
                for block in response.content:
                    if isinstance(block, TextBlock):
                        display_text.append(block.text)
                        final_text += block.text
                log("agent_response", {"content": final_text}, session_id)
                display_text.append("\n\n✅  Task completed.", style="bold green")
                refresh()
                break

            if response.stop_reason == "tool_use":
                tool_responses = []

                for block in response.content:
                    if isinstance(block, TextBlock) and block.text:
                        display_text.append(block.text)
                        refresh()

                    if isinstance(block, ToolUseBlock):
                        log("tool_call", {"tool": block.name, "input": block.input}, session_id)
                        display_text.append("\n")
                        if block.name == "web_search":
                            query = block.input.get("query", "")
                            display_text.append("🌐  Web Search: ", style="bold yellow")
                            display_text.append(f'"{query}"\n', style="italic yellow")
                        elif block.name == "write_file":
                            fname = block.input.get("file_name", "")
                            display_text.append("📝  Writing file: ", style="bold blue")
                            display_text.append(f"{fname}\n", style="blue")
                        elif block.name == "read_file":
                            fname = block.input.get("file_name", "")
                            display_text.append("📖  Reading file: ", style="bold blue")
                            display_text.append(f"{fname}\n", style="blue")
                        else:
                            display_text.append(f"🔧  Tool: {block.name}\n", style="bold")
                        refresh()

                        tool_result = tool_executor(block)
                        tool_responses.append(tool_result)
                        log("tool_result", {"tool": block.name, "success": not tool_result["is_error"], "content": tool_result["content"]}, session_id)

                        if not tool_result["is_error"]:
                            if block.name == "write_file":
                                fname = block.input.get("file_name", "")
                                display_text.append(f"    ✅  Saved: {fname}\n", style="green")
                            elif block.name == "read_file":
                                display_text.append("    ✅  Read successfully\n", style="green")
                            else:
                                display_text.append("    ✅  Done\n", style="green")
                        else:
                            display_text.append(
                                f"    ❌  Error: {tool_result['content'][:100]}\n", style="red"
                            )
                        refresh()

                agent_messages = agent_messages + [{"role": "user", "content": tool_responses}]
            else:
                break

    return agent_messages


def main():
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🔬 AI Research Agent[/bold cyan]\n"
            "[dim]Web Search  ·  File Reading  ·  File Writing[/dim]\n"
            "[dim]Type [/dim][bold]quit[/bold][dim] or [/dim][bold]exit[/bold][dim] to stop[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()

    agent_messages = []
    session_id = str(uuid.uuid4())[:8]
    log("session_start", {}, session_id)
    console.print(f"[dim]Session ID: {session_id}  ·  Log: {LOG_FILE}[/dim]\n")

    while True:
        console.print(Rule(style="dim"))
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! 👋[/dim]\n")
            break

        if user_input.strip().lower() in ("quit", "exit", "q"):
            console.print("\n[dim]Goodbye! 👋[/dim]\n")
            break

        if not user_input.strip():
            continue

        console.print()
        try:
            agent_messages = run_agent(user_input, agent_messages, session_id)
        except Exception as e:
            log("error", {"message": str(e)}, session_id)
            console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")
        console.print()

    log("session_end", {}, session_id)


if __name__ == "__main__":
    main()
