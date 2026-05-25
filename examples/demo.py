"""
Quick demo — shows the Agent handling a multi-step task.
Run: python examples/demo.py
"""
import sys
sys.path.insert(0, ".")

from agent import Agent

agent = Agent()

tasks = [
    "用 Python 计算前 20 个斐波那契数列，并找出其中的质数",
    "把上面的结果写入文件 output/fibonacci_primes.txt",
    "列出当前目录下的所有文件",
]

for task in tasks:
    print(f"\n{'='*60}")
    print(f"用户: {task}")
    print(f"{'='*60}")
    response = agent.chat(task)
    print(f"Agent: {response}")
