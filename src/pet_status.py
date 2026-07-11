"""PetStatusEngine: manages pet hunger and foraging/normal state."""
from PyQt6.QtCore import QTimer, QObject


class PetStatusEngine(QObject):
    """Tracks pet hunger level (0-100) and determines normal / foraging state.

    Hunger decays by 2 every 10 seconds. Feed the pet to restore hunger.
    """

    _HUNGER_DECAY_RATE = 2       # points per tick
    _HUNGER_DECAY_INTERVAL = 30_000  # ms — 每30秒衰减2点
    _HUNGER_FEED_AMOUNT = 30     # points restored per feed
    _HUNGER_MAX = 100
    _HUNGER_MIN = 0
    _HUNGER_THRESHOLD = 20       # below this → foraging

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self.hunger: int = 80          # 0-100
        self.state: str = "normal"     # "normal" | "foraging"

        # ── Decay timer ──────────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start(self._HUNGER_DECAY_INTERVAL)

        print(f"[状态引擎] 初始化完成 — 饥饿值: {self.hunger}, 状态: {self.state}")

    # ──────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────

    def _on_timer_tick(self) -> None:
        """Called every 10 s: decrease hunger and re-evaluate state."""
        self.hunger = max(self._HUNGER_MIN, self.hunger - self._HUNGER_DECAY_RATE)
        self.update_state()

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def update_state(self) -> None:
        """Re-evaluate state based on current hunger. Print on change."""
        if self.hunger >= self._HUNGER_THRESHOLD:
            new_state = "normal"
        else:
            new_state = "foraging"

        if new_state != self.state:
            self.state = new_state
            print(f"[状态变更] 饥饿值: {self.hunger}, 当前状态: {self.state}")

    def feed_pet(self) -> None:
        """Feed the pet: restore 30 hunger (max 100) and re-evaluate state."""
        self.hunger = min(self._HUNGER_MAX, self.hunger + self._HUNGER_FEED_AMOUNT)
        self.update_state()
        print(f"[喂食] 当前饥饿值: {self.hunger}")
