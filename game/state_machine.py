"""State-machine core for the game flow."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class StateMachineError(Exception):
    """Raised when the state machine receives an invalid transition request."""


@dataclass
class StateResult:
    """Result returned by a state after handling player input."""

    text: str = ""
    next_state: Optional[str] = None
    should_continue: bool = True
    push_state: Optional[str] = None
    pop_state: bool = False
    transition_notice: str = ""
    prompt: str = ""
    resume_stage: str = ""


class GameState(ABC):
    """Base interface for states that own local game flow."""

    @property
    @abstractmethod
    def state_id(self) -> str:
        """Stable state identifier used by the StateMachine registry."""

    @abstractmethod
    def get_available_actions(self, ctx) -> list:
        """Return actions available in this state."""

    @abstractmethod
    def handle_action(self, ctx, action: str) -> StateResult:
        """Handle player input and return a state result."""

    def on_enter(self, ctx, from_state: Optional[str] = None) -> str:
        """Return optional text shown after entering this state."""
        return ""

    def on_exit(self, ctx, to_state: str) -> None:
        """Clean up before leaving this state."""

    def on_update(self, ctx) -> Optional[str]:
        """Run optional per-turn update behavior."""
        return None


class StateMachine:
    """Owns current state, state registry, and stack-based interruptions."""

    def __init__(self, initial_state: GameState, context, states: Optional[dict] = None):
        self.context = context
        self._states = {}
        self._state_stack = []
        self._current = initial_state
        self.register(initial_state)
        if states:
            for state in states.values():
                self.register(state)

    @property
    def current(self) -> GameState:
        """Return the active state."""
        return self._current

    @property
    def state_stack(self) -> list:
        """Return a copy of the interruption stack."""
        return list(self._state_stack)

    def register(self, state: GameState) -> None:
        """Register a state by its stable identifier."""
        self._states[state.state_id] = state

    def get_available_actions(self) -> list:
        """Return actions available in the current state."""
        return self._current.get_available_actions(self.context)

    def handle_action(self, action: str) -> StateResult:
        """Delegate input to the current state and apply any requested transition."""
        result = self._current.handle_action(self.context, action)
        return self._apply_result(result)

    def transition_to(self, state_id: str) -> str:
        """Transition to a registered state and return its enter text."""
        if state_id not in self._states:
            raise StateMachineError(f"Unknown state: {state_id}")

        previous_id = self._current.state_id
        self._current.on_exit(self.context, state_id)
        self._current = self._states[state_id]
        return self._current.on_enter(self.context, previous_id)

    def push(self, state_id: str) -> str:
        """Push the current state and transition to another state."""
        if state_id not in self._states:
            raise StateMachineError(f"Unknown state: {state_id}")
        self._state_stack.append(self._current)
        return self.transition_to(state_id)

    def pop(self) -> str:
        """Restore the most recent interrupted state."""
        if not self._state_stack:
            raise StateMachineError("State stack underflow")
        target = self._state_stack.pop()
        previous_id = self._current.state_id
        self._current.on_exit(self.context, target.state_id)
        self._current = target
        return self._current.on_enter(self.context, previous_id)

    def _apply_result(self, result: StateResult) -> StateResult:
        """Apply transition fields while preserving player-facing result text."""
        transition_text = ""
        if result.push_state:
            transition_text = self.push(result.push_state)
        elif result.pop_state:
            transition_text = self.pop()
        elif result.next_state:
            transition_text = self.transition_to(result.next_state)

        if transition_text:
            result.transition_notice = "\n".join(
                text for text in [result.transition_notice, transition_text] if text
            )
        return result
