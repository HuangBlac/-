"""Explicit dependency container for game states."""

from dataclasses import dataclass


@dataclass
class GameContext:
    """Dependencies that states may use to read and mutate game data."""

    player: object
    course_system: object
    exam_system: object
    research_system: object
    event_system: object
    mutation_system: object
    graduation_thesis: object
    advisor_system: object
    game_state: object
    log_func: object
    trigger_event: object
    apply_event_result: object
