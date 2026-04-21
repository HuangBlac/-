import unittest
from unittest.mock import patch

from game.character import CheckResult, ResearchDirection
from game.event_system import EventSystem
from game.game_engine import GameEngine
from game.research import IdeaStatus


class MinimumLoopTest(unittest.TestCase):
    def test_course_selection_waits_for_input_without_extra_action_cost(self):
        game = GameEngine("tester")
        game.start_game()

        self.assertEqual(game.player.action_points, 2)
        self.assertEqual(game.player.max_action_points, 2)

        game.message_log.clear()
        self.assertTrue(game.do_action("1"))

        self.assertTrue(game.action_system.awaiting_course_selection)
        self.assertEqual(game.player.action_points, 1)

        game.message_log.clear()
        self.assertTrue(game.do_action("1 2 3"))

        self.assertFalse(game.action_system.awaiting_course_selection)
        self.assertTrue(game.player.courses_selected)
        self.assertEqual(game.player.action_points, 1)

    def test_research_can_start_after_first_semester_unlock_before_year_two(self):
        game = GameEngine("tester")
        game.start_game()
        game.player.research_unlocked = True
        game.player.research_direction = ResearchDirection.ARCANE_ANALYSIS

        self.assertEqual(game.player.year, 1)
        self.assertTrue(game.research_system.can_start_research())

        action_ids = {action_id for action_id, _, _ in game.get_actions()}
        self.assertIn("2", action_ids)

    def test_random_events_load_without_missing_file_warning(self):
        event_system = EventSystem()

        self.assertGreater(len(event_system.get_events("random")), 0)

    def test_read_literature_generates_and_evaluates_idea_after_unlock(self):
        game = GameEngine("tester")
        game.start_game()
        game.player.research_unlocked = True
        game.player.research_direction = ResearchDirection.ARCANE_ANALYSIS
        game.research_system.literature_progress = 100

        with patch(
            "game.research.ability_check",
            side_effect=[
                (CheckResult.CRITICAL_SUCCESS, 1),
                (CheckResult.CRITICAL_SUCCESS, 1),
            ],
        ):
            result = game.research_system.read_literature()

        self.assertIn("idea", result)
        self.assertEqual(len(game.research_system.ideas), 1)
        self.assertEqual(game.research_system.ideas[0].status, IdeaStatus.RAW)

        eval_result = game.research_system.evaluate_idea(0, "accept")

        self.assertIn("初步想法", eval_result)
        self.assertEqual(game.research_system.ideas[0].status, IdeaStatus.PRELIMINARY)


if __name__ == "__main__":
    unittest.main()
