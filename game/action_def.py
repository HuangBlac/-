"""Action definition model for state-driven menus."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionDef:
    """A player-facing action available in the current state."""

    key: str
    label: str
    description: str
    costs_action_point: bool = True
    requires_confirmation: bool = False

    def as_tuple(self) -> tuple:
        """Return the legacy ConsoleUI-compatible action tuple."""
        return (self.key, self.label, self.description)
