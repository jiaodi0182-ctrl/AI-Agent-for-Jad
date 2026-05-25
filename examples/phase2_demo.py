"""
Phase 2 demo — shows long-term memory + multi-step planning + streaming.
Run: python examples/phase2_demo.py
"""
import sys
sys.path.insert(0, ".")

from agent import Agent, LongTermMemory, Planner

ltm = LongTermMemory()
agent = Agent(long_term_memory=ltm)
planner = Planner(agent)

# --- Demo 1: streaming output ---
print("=" * 60)
print("Demo 1: 流式输出")
print("=" * 60)
print("Agent: ", end="", flush=True)
for chunk in agent.stream("用一句话介绍量子计算"):
    print(chunk, end="", flush=True)
print()

# --- Demo 2: long-term memory recall ---
print("\n" + "=" * 60)
print("Demo 2: 长期记忆")
print("=" * 60)
agent.chat("我叫 Jad，我喜欢喝咖啡和写 Python 代码。")
agent.reset()  # 清除短期记忆，但长期记忆保留

new_agent = Agent(long_term_memory=ltm)
response = new_agent.chat("你还记得我的名字和爱好吗？")
print(f"Agent: {response}")

# --- Demo 3: multi-step planner ---
print("\n" + "=" * 60)
print("Demo 3: 多步规划")
print("=" * 60)

def show_step(i, total, step, result):
    print(f"  [{i}/{total}] {step[:60]}...")

result = planner.run(
    "用 Python 生成1到100之间的所有质数，计算它们的总和，然后把结果保存到文件 output/primes.txt",
    on_step=show_step,
)
print(f"\n最终结果: {result}")
