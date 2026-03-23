class ReputationModule:
    def __init__(self) -> None:
        self._reputation = 0

    def update_after_race(self, position: int) -> int:
        gain = max(0, 6 - position)
        self._reputation += gain
        return self._reputation

    def update_after_mission(self, success: bool) -> int:
        self._reputation += 3 if success else -2
        return self._reputation

    def get_reputation(self) -> int:
        return self._reputation
