import os
from collections.abc import Iterator

import anthropic
from dotenv import load_dotenv

from .memory import Memory
from tools import TOOLS, execute_tool

load_dotenv()

_BASE_SYSTEM = """You are Jad's personal AI agent. You are helpful, direct, and efficient.

You have access to the following tools:
- web_search: Search the internet for current information
- read_file / write_file: Read and write files on the local filesystem
- run_python: Execute Python code for calculations and data tasks
- list_directory: Browse the filesystem

Think step by step. When a task requires multiple steps, plan and execute them in sequence.
Always use tools when they would give better results than your training knowledge alone.
Respond in the same language the user writes in."""

_CHINESE_SYSTEM = """你是 Jad 的私人 AI 助手。你聪明、高效、直接，始终以中文回复。

你可以使用以下工具：
- web_search：搜索互联网获取最新信息
- read_file / write_file：读写本地文件系统中的文件
- run_python：执行 Python 代码进行计算和数据处理
- list_directory：浏览文件系统目录

遇到复杂任务时，先逐步思考再分步执行。
当工具能提供比训练知识更好的结果时，优先使用工具。
始终使用中文回复，保持回答简洁清晰。"""

LANGUAGE_SYSTEMS = {
    "en": _BASE_SYSTEM,
    "zh": _CHINESE_SYSTEM,
}


class Agent:
    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 4096,
        long_term_memory=None,
        language: str = "zh",
    ):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.memory = Memory()
        self.ltm = long_term_memory  # optional LongTermMemory instance
        self.language = language if language in LANGUAGE_SYSTEMS else "en"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, user_message: str) -> str:
        """Send a message and return the full response string."""
        self.memory.add("user", user_message)
        if self.ltm:
            self.ltm.save("user", user_message)
        result = self._run_loop(user_message)
        if self.ltm:
            self.ltm.save("assistant", result)
        return result

    def stream(self, user_message: str) -> Iterator[str]:
        """Send a message and yield response text token by token."""
        self.memory.add("user", user_message)
        if self.ltm:
            self.ltm.save("user", user_message)
        full_response = ""
        for chunk in self._stream_loop(user_message):
            full_response += chunk
            yield chunk
        if self.ltm:
            self.ltm.save("assistant", full_response)

    def reset(self):
        self.memory.clear()
        print("短期记忆已清除。")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def set_language(self, language: str):
        """Switch the system language. Supported: 'en' (English), 'zh' (Chinese)."""
        if language in LANGUAGE_SYSTEMS:
            self.language = language

    def _build_system_prompt(self, user_message: str) -> str:
        base = LANGUAGE_SYSTEMS[self.language]
        if not self.ltm:
            return base
        relevant = self.ltm.format_for_prompt(user_message)
        if relevant:
            return f"{base}\n\n{relevant}"
        return base

    def _run_loop(self, user_message: str) -> str:
        system = self._build_system_prompt(user_message)
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system,
                tools=TOOLS,
                messages=self.memory.get(),
            )

            text_parts = [b.text for b in response.content if b.type == "text"]
            final_text = "\n".join(text_parts).strip()

            if response.stop_reason == "end_turn":
                self.memory.add("assistant", response.content)
                return final_text

            if response.stop_reason == "tool_use":
                self.memory.add("assistant", response.content)
                tool_results = self._execute_tools(response.content)
                self.memory.add("user", tool_results)
                continue

            self.memory.add("assistant", response.content)
            return final_text or "(no response)"

    def _stream_loop(self, user_message: str) -> Iterator[str]:
        """Streaming version — yields text chunks; handles tool_use transparently."""
        system = self._build_system_prompt(user_message)

        while True:
            accumulated_content = []
            stop_reason = None
            current_text = ""

            with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system,
                tools=TOOLS,
                messages=self.memory.get(),
            ) as stream:
                for event in stream:
                    event_type = type(event).__name__

                    if event_type == "RawContentBlockDeltaEvent":
                        delta = event.delta
                        if hasattr(delta, "text"):
                            yield delta.text
                            current_text += delta.text

                response = stream.get_final_message()
                accumulated_content = response.content
                stop_reason = response.stop_reason

            if stop_reason == "end_turn":
                self.memory.add("assistant", accumulated_content)
                return

            if stop_reason == "tool_use":
                self.memory.add("assistant", accumulated_content)
                tool_results = self._execute_tools(accumulated_content)
                # Yield tool activity indicator
                for r in tool_results:
                    tool_name = next(
                        (b.name for b in accumulated_content if b.type == "tool_use" and b.id == r["tool_use_id"]),
                        "tool",
                    )
                    yield f"\n[使用工具: {tool_name}]\n"
                self.memory.add("user", tool_results)
                continue

            self.memory.add("assistant", accumulated_content)
            return

    def _execute_tools(self, content_blocks) -> list[dict]:
        results = []
        for block in content_blocks:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        return results
