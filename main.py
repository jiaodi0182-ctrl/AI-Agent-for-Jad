#!/usr/bin/env python3
"""
AI Agent for Jad — interactive CLI
Usage: python main.py
Commands: 'exit' to quit, 'reset' to clear memory, 'lang zh/en' to switch language
"""
import sys
sys.path.insert(0, ".")

from agent import Agent

LANG_LABELS = {
    "en": "English",
    "zh": "中文",
}

HELP_TEXT = {
    "en": "Commands: 'exit' quit | 'reset' clear memory | 'lang zh' switch to Chinese",
    "zh": "命令：'exit' 退出 | 'reset' 清除记忆 | 'lang en' 切换英文",
}

PROMPT_LABEL = {
    "en": "You",
    "zh": "你",
}

GOODBYE = {
    "en": "Goodbye!",
    "zh": "再见！",
}


def main():
    print("=" * 40)
    print("AI Agent for Jad")
    print("输入 'lang zh' 切换中文 | Type 'lang en' for English")
    print("=" * 40)

    try:
        agent = Agent()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    lang = "zh"
    print(HELP_TEXT[lang])

    while True:
        try:
            user_input = input(f"\n{PROMPT_LABEL[lang]}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{GOODBYE[lang]}")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print(GOODBYE[lang])
            break

        if user_input.lower() == "reset":
            agent.reset()
            continue

        if user_input.lower().startswith("lang "):
            new_lang = user_input.split()[1].lower()
            if new_lang in LANG_LABELS:
                lang = new_lang
                agent.set_language(lang)
                print(f"[语言已切换为 {LANG_LABELS[lang]} / Language set to {LANG_LABELS[lang]}]")
                print(HELP_TEXT[lang])
            else:
                print(f"[不支持的语言。支持: {', '.join(LANG_LABELS.keys())}]")
            continue

        try:
            response = agent.chat(user_input)
            print(f"\nAgent: {response}")
        except Exception as e:
            print(f"\n{'错误' if lang == 'zh' else 'Error'}: {e}")


if __name__ == "__main__":
    main()
