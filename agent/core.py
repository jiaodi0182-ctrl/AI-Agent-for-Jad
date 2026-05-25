import os
import anthropic
from dotenv import load_dotenv

from .memory import Memory
from tools import TOOLS, execute_tool

load_dotenv()

SYSTEM_PROMPT = """You are Jad's personal AI agent. You are helpful, direct, and efficient.

You have access to the following tools:
- web_search: Search the internet for current information
- read_file / write_file: Read and write files on the local filesystem
- run_python: Execute Python code for calculations and data tasks
- list_directory: Browse the filesystem

Think step by step. When a task requires multiple steps, plan and execute them in sequence.
Always use tools when they would give better results than your training knowledge alone.
Respond in the same language the user writes in."""


class Agent:
    def __init__(self, model: str = "claude-sonnet-4-6", max_tokens: int = 4096):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.memory = Memory()

    def chat(self, user_message: str) -> str:
        self.memory.add("user", user_message)
        return self._run_loop()

    def _run_loop(self) -> str:
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.memory.get(),
            )

            # Collect any text from this response turn
            text_parts = [b.text for b in response.content if b.type == "text"]
            final_text = "\n".join(text_parts).strip()

            if response.stop_reason == "end_turn":
                self.memory.add("assistant", response.content)
                return final_text

            if response.stop_reason == "tool_use":
                self.memory.add("assistant", response.content)
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                self.memory.add("user", tool_results)
                continue

            # Unexpected stop reason — return what we have
            self.memory.add("assistant", response.content)
            return final_text or "(no response)"

    def reset(self):
        self.memory.clear()
        print("Memory cleared.")
