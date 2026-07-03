"""PetStateMachine: pure-logic state transitions driven by cursor behavior.

No QObject inheritance — state changes are detected by comparing
current_state before/after update() in the game loop.
"""
from enum import Enum, auto


class PetState(Enum):
    """The four base states the pet can be in."""
    IDLE = auto()
    FOLLOWING = auto()
    RUNNING = auto()
    EXCITED = auto()
    DRAGGED = auto()


class PetStateMachine:
    """Pure-Python state machine that reads cursor metrics and returns a pet state.

    State priority (highest wins):
        RUNNING > EXCITED > IDLE > FOLLOWING
    """

    # Thresholds
    _RUN_SPEED = 600       # px/s — above this → RUNNING
    _EXCITED_DIST = 150    # px   — closer than this → EXCITED candidate
    _STILL_SPEED = 5       # px/s — below this, cursor is "still"
    _IDLE_DURATION = 2.0   # s    — still for this long → IDLE

    def __init__(self) -> None:
        self.current_state: PetState = PetState.FOLLOWING

    def update(
        self,
        cursor_speed: float,
        distance_to_pet: float,
        mouse_still_duration: float,
    ) -> PetState:
        """Evaluate conditions in priority order and return the new state.

        Args:
            cursor_speed: Instantaneous cursor speed in px/s.
            distance_to_pet: Distance from cursor to pet window centre in px.
            mouse_still_duration: Seconds the cursor has been near-stationary.

        Returns:
            The resolved PetState for this tick.
        """
        # 1. RUNNING — highest priority
        if cursor_speed > self._RUN_SPEED:
            self.current_state = PetState.RUNNING
            return self.current_state

        # 2. EXCITED — cursor near pet AND moving
        if distance_to_pet < self._EXCITED_DIST and cursor_speed > self._STILL_SPEED:
            self.current_state = PetState.EXCITED
            return self.current_state

        # 3. IDLE — cursor has been still long enough
        if mouse_still_duration > self._IDLE_DURATION:
            self.current_state = PetState.IDLE
            return self.current_state

        # 4. FOLLOWING — cursor is moving (below RUN threshold)
        if cursor_speed > self._STILL_SPEED:
            self.current_state = PetState.FOLLOWING
            return self.current_state

        # No condition matched — keep previous state
        # (e.g., speed=0 but still_duration < 2.0 → stay in FOLLOWING a moment longer)
        return self.current_state
