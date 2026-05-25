class Memory:
    def __init__(self, max_turns: int = 20):
        self._history: list[dict] = []
        self.max_turns = max_turns

    def add(self, role: str, content):
        self._history.append({"role": role, "content": content})
        # Keep only the last max_turns exchanges (2 messages per turn)
        if len(self._history) > self.max_turns * 2:
            self._history = self._history[-(self.max_turns * 2):]

    def get(self) -> list[dict]:
        return list(self._history)

    def clear(self):
        self._history = []

    def __len__(self):
        return len(self._history)
