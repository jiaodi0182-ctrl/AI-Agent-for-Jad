#!/usr/bin/env python3
"""
AI Agent for Jad — interactive CLI
Usage: python main.py
Commands: 'exit' to quit, 'reset' to clear memory
"""
import sys
sys.path.insert(0, ".")

from agent import Agent


def main():
    print("AI Agent for Jad")
    print("输入 'exit' 退出，输入 'reset' 清除对话记忆")
    print("-" * 40)

    try:
        agent = Agent()
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("再见！")
            break
        if user_input.lower() == "reset":
            agent.reset()
            continue

        try:
            response = agent.chat(user_input)
            print(f"\nAgent: {response}")
        except Exception as e:
            print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
