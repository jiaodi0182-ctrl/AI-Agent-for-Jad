"""
Multi-step task planner using Plan-and-Execute pattern.

1. PLAN  — ask Claude to decompose the task into ordered steps
2. EXECUTE — run each step with the Agent, passing prior results as context
3. SUMMARIZE — synthesize a final answer from all step outputs
"""
import json
import re
import anthropic


_PLAN_SYSTEM = """You are a task planning assistant.
Given a complex task, output a JSON array of clear, concrete steps to complete it.
Each step should be actionable and self-contained.
Output ONLY valid JSON — an array of strings. No markdown, no explanation.
Example: ["Step 1: ...", "Step 2: ...", "Step 3: ..."]"""

_SUMMARIZE_SYSTEM = """You are a synthesis assistant.
Given a task and the outputs from each step of its execution,
write a clear, concise final answer that addresses the original task.
Respond in the same language the user used."""


class Planner:
    def __init__(self, agent):
        self.agent = agent

    def run(self, task: str, on_step=None) -> str:
        """
        Execute a complex task via plan-then-execute.
        on_step(step_num, total, step_text, result) is called after each step (optional).
        Returns the final synthesized answer.
        """
        steps = self._plan(task)
        if not steps:
            return self.agent.chat(task)

        step_results = []
        for i, step in enumerate(steps, 1):
            context = self._build_context(task, step_results, step)
            result = self.agent.chat(context)
            step_results.append({"step": step, "result": result})
            if on_step:
                on_step(i, len(steps), step, result)

        return self._summarize(task, step_results)

    def _plan(self, task: str) -> list[str]:
        response = self.agent.client.messages.create(
            model=self.agent.model,
            max_tokens=1024,
            system=_PLAN_SYSTEM,
            messages=[{"role": "user", "content": task}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        try:
            steps = json.loads(raw)
            if isinstance(steps, list) and all(isinstance(s, str) for s in steps):
                return steps
        except json.JSONDecodeError:
            pass
        # Fallback: treat as single-step
        return [task]

    def _build_context(self, task: str, prior: list[dict], current_step: str) -> str:
        parts = [f"总体任务: {task}", f"\n当前步骤: {current_step}"]
        if prior:
            parts.append("\n已完成的步骤:")
            for p in prior:
                parts.append(f"  - {p['step']}\n    结果: {p['result'][:300]}")
        parts.append("\n请执行当前步骤。")
        return "\n".join(parts)

    def _summarize(self, task: str, step_results: list[dict]) -> str:
        steps_text = "\n".join(
            f"步骤 {i}: {s['step']}\n结果: {s['result']}"
            for i, s in enumerate(step_results, 1)
        )
        prompt = f"原始任务: {task}\n\n各步骤执行结果:\n{steps_text}"
        response = self.agent.client.messages.create(
            model=self.agent.model,
            max_tokens=2048,
            system=_SUMMARIZE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
