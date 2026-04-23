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

    def test_year_two_does_not_unlock_research_without_exam_unlock(self):
        game = GameEngine("tester")
        game.start_game()
        game.player.year = 2
        game.player.research_unlocked = False
        game.player.research_direction = ResearchDirection.ARCANE_ANALYSIS

        self.assertFalse(game.research_system.can_start_research())

        action_ids = {action_id for action_id, _, _ in game.get_actions()}
        self.assertNotIn("2", action_ids)

    def test_failed_final_exam_does_not_assign_research_direction(self):
        game = GameEngine("tester")
        game.start_game()

        with patch("game.course.ability_check", return_value=(CheckResult.FAILURE, 90)):
            result = game.action_system.handlers["course"]._do_final_exam()

        self.assertFalse(game.player.research_unlocked)
        self.assertIsNone(game.player.research_direction)
        self.assertIn("暂未解锁科研方向", result)

    def test_passed_final_exam_unlocks_research_and_assigns_direction(self):
        game = GameEngine("tester")
        game.start_game()

        with patch("game.course.ability_check", return_value=(CheckResult.SUCCESS, 1)):
            game.action_system.handlers["course"]._do_final_exam()

        self.assertTrue(game.player.research_unlocked)
        self.assertIsNotNone(game.player.research_direction)

    def test_random_events_load_without_missing_file_warning(self):
        event_system = EventSystem()

        self.assertGreater(len(event_system.get_events("random")), 0)

    def test_event_progress_updates_inspiration_with_bounds(self):
        game = GameEngine("tester")
        game.start_game()
        event_system = EventSystem()

        game.player.research_progress = 250
        result = event_system.apply_event_effect(game.player, {"effect": {"progress": 20}})

        self.assertEqual(game.player.research_progress, 255)
        self.assertIn("灵感+20", result)

        game.player.research_progress = 3
        event_system.apply_event_effect(game.player, {"effect": {"progress": -10}})

        self.assertEqual(game.player.research_progress, 0)

    def test_holiday_study_caps_inspiration_value(self):
        game = GameEngine("tester")
        game.start_game()
        game.player.advisor = None
        game.player.research_progress = 250

        result = game.action_system.handlers["entertainment"].handle("4")

        self.assertEqual(game.player.research_progress, 255)
        self.assertIn("灵感+10", result)

    def test_inspiration_burst_waits_for_research_direction(self):
        game = GameEngine("tester")
        game.start_game()
        game.player.research_progress = 120
        game.player.research_direction = None

        game._trigger_inspiration_burst()

        self.assertEqual(game.player.research_progress, 120)
        self.assertEqual(len(game.research_system.ideas), 0)

    def test_inspiration_burst_generates_raw_idea_without_resetting_literature_progress(self):
        game = GameEngine("tester")
        game.start_game()
        game.player.research_unlocked = True
        game.player.research_direction = ResearchDirection.ARCANE_ANALYSIS
        game.player.research_progress = 100
        game.player.sanity = 100
        game.research_system.literature_progress = 42

        with patch("game.research.ability_check", return_value=(CheckResult.SUCCESS, 1)), \
             patch("game.research.random.choice", return_value=("测试灵感", "用于测试的灵感idea", 1)), \
             patch("game.game_engine.random.randint", side_effect=[50, 5]):
            game._trigger_inspiration_burst()

        self.assertEqual(game.player.research_progress, 50)
        self.assertEqual(game.player.sanity, 95)
        self.assertEqual(game.research_system.literature_progress, 42)
        self.assertEqual(len(game.research_system.ideas), 1)
        self.assertEqual(game.research_system.ideas[0].status, IdeaStatus.RAW)
        self.assertTrue(any("灵感爆发" in message for message in game.message_log))

    def test_inspiration_burst_triggers_once_per_action_even_if_progress_remains_high(self):
        game = GameEngine("tester")
        game.start_game()
        game.player.research_unlocked = True
        game.player.research_direction = ResearchDirection.ARCANE_ANALYSIS
        game.player.research_progress = 200
        game.player.sanity = 100

        with patch("game.research.ability_check", return_value=(CheckResult.SUCCESS, 1)), \
             patch("game.research.random.choice", return_value=("测试灵感", "用于测试的灵感idea", 1)), \
             patch("game.game_engine.random.random", return_value=1.0), \
             patch("game.game_engine.random.randint", side_effect=[1, 5]):
            self.assertTrue(game.do_action("3"))

        self.assertEqual(game.player.research_progress, 199)
        self.assertEqual(len(game.research_system.ideas), 1)

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
