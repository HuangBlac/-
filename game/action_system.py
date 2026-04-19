"""行动系统 - 模块化行动处理器"""
import random

from .character import SemesterType, ResearchDirection
from .action_handlers import ActionHandlerFactory


class ActionSystem:
    """行动系统管理器 - 使用模块化处理器"""

    def __init__(self, player, course_system, research_system, graduation_thesis, npcs):
        self.player = player
        self.course_system = course_system
        self.research_system = research_system
        self.graduation_thesis = graduation_thesis
        self.npcs = npcs

        # 初始化各类型行动处理器
        self.handlers = ActionHandlerFactory.get_all_handlers(self)

        # 状态标记
        self.exam_done = False  # 期末考试是否已完成
        self.awaiting_course_selection = False  # 是否正在等待选课
        self.awaiting_entertainment_selection = False  # 是否正在等待娱乐选择

    def do_action(self, action: str, log_func) -> tuple:
        """执行行动

        Args:
            action: 行动代码
            log_func: 日志记录函数

        Returns:
            (action_result: str, should_continue: bool)
        """
        # 处理选课输入
        if self.awaiting_course_selection:
            return self._handle_course_selection(action, log_func)

        # 处理娱乐选择
        if self.awaiting_entertainment_selection:
            return self._handle_entertainment_selection(action, log_func)

        # 判断当前阶段
        in_research = self.player.year >= 2 or self.course_system.first_semester_completed
        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        # 根据阶段分发行动
        if not in_research and not is_holiday:
            # 课程阶段
            handler = self.handlers["course"]
            result = handler.handle(action)
            return (result, True)
        elif is_holiday:
            # 假期阶段 - 显示娱乐选项
            return self._handle_holiday_action(action, log_func)
        else:
            # 科研阶段
            if action.lower() == "e":
                return ("__EVALUATE_IDEA__", True)
            handler = self.handlers["research"]
            result = handler.handle(action)
            return (result, True)

    def _handle_holiday_action(self, action: str, log_func) -> tuple:
        """处理假期行动"""
        # 假期行动
        holiday_actions = {
            "1": ("旅游", 20, 0),
            "2": ("回家", 25, 0),
            "3": ("娱乐", 15, 0),
            "4": ("学习", 5, 10),
            "9": ("休息", 18, 0),
        }

        if action not in holiday_actions:
            return ("无效选择，请重试", True)

        name, san, progress = holiday_actions[action]

        # 高压导师假期任务检查
        if self.player.advisor and self.player.advisor.personality_value >= 61:
            if random.random() < 0.3:
                task, task_san, task_progress = random.choice([
                    ("导师安排任务", -15, 15),
                    ("远程组会", -10, 5),
                    ("紧急数据", -12, 10),
                ])
                self.player.change_sanity(task_san)
                self.player.research_progress += task_progress
                return (f"【{task}】\n理智{task_san}，研究进度+{task_progress}\n假期泡汤了...", True)

        self.player.change_sanity(san)
        self.player.research_progress += progress
        return (f"你{name}了几天\n理智+{san}" + (f"，研究进度+{progress}" if progress else ""), True)

    def _handle_course_selection(self, selection: str, log_func) -> tuple:
        """处理选课输入"""
        self.awaiting_course_selection = False

        try:
            # 解析输入，如 "1 2 3"
            selections = [int(x.strip()) for x in selection.split() if x.strip().isdigit()]

            if len(selections) != 3:
                log_func("请选择3门选修课！")
                self.awaiting_course_selection = True
                return ("请输入3个编号（如：1 2 3）", True)

            success = self.course_system.select_electives(selections)

            if success:
                self.player.courses_selected = True
                log_func(f"选课完成！你选择了：")
                for c in self.course_system.selected_electives:
                    log_func(f"  - {c.name}")
                return ("选课完成！", True)
            else:
                log_func("选课失败，请重试！")
                self.awaiting_course_selection = True
                return (self.course_system.get_course_selection_menu(), True)

        except (ValueError, IndexError):
            log_func("输入格式错误！")
            self.awaiting_course_selection = True
            return ("请输入3个编号（如：1 2 3）", True)

    def _handle_entertainment_selection(self, selection: str, log_func) -> tuple:
        """处理娱乐选择"""
        self.awaiting_entertainment_selection = False

        entertainment = {
            "1": ("听音乐", 8, 0, 0),
            "2": ("玩游戏", 10, -5, 0),
            "3": ("打篮球", 12, 0, 1),
            "4": ("看电影", 10, 0, 0),
            "5": ("社交", 6, 0, 0),
        }

        if selection not in entertainment:
            return ("无效选择", True)

        name, san, progress, str_bon = entertainment[selection]
        self.player.change_sanity(san)
        self.player.research_progress += progress
        if str_bon:
            self.player.STR += str_bon

        result = f"你{name}了\n理智+{san}"
        if progress:
            result += f"，研究进度{progress:+d}"
        if str_bon:
            result += f"，STR+{str_bon}"

        return (result, True)

    def handle_debug_action(self, action: str, log_func) -> bool:
        """处理Debug行动"""
        if action == "a" or action == "A":
            self.player.advance_week()
            log_func(f"[DEBUG] 时间快进：现在是第{self.player.year}学年 {self.player.semester_name} 第{self.player.week_in_semester}周")
            return True
        elif action == "b" or action == "B":
            self._debug_go_to_year2(log_func)
            return True
        elif action.lower() == "m":
            self.player.mutation += 1
            log_func(f"[DEBUG] 异变值+1，当前异变值: {self.player.mutation:.2f} ({self.player.mutation_level})")
            return True
        return False

    def _debug_go_to_year2(self, log_func):
        """Debug功能：跳转到研二"""
        self.player.year = 2
        self.player.semester = SemesterType.SPRING
        self.player.week_in_semester = 1
        self.player.courses_selected = True
        self.course_system.first_semester_completed = True

        if not self.player.research_direction:
            self.player.research_direction = random.choice(list(ResearchDirection))

        self.player.reset_action_points()

        log_func("[DEBUG] ===== 跳转到研二 =====")
        log_func(f"当前状态：{self.player.year_name} {self.player.semester_name} 第{self.player.week_in_semester}周")
        log_func(f"研究方向：{self.player.research_direction.value}")
        log_func(f"INT:{self.player.INT} | SEN:{self.player.SEN} | EDU:{self.player.EDU}")
        log_func(f"STR:{self.player.STR} | SOC:{self.player.SOC} | 声望:{self.player.reputation}")
        log_func("你现在可以开始阅读文献获取idea了！")
        log_func("按2阅读文献 -> 获得idea -> 按E评估 -> 按3实验 -> 按4写初稿 -> 按5投稿")

    def get_actions(self) -> list:
        """获取可选行动"""
        actions = []

        in_research = self.player.year >= 2 or self.course_system.first_semester_completed
        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        # 课程阶段
        if not in_research and not is_holiday:
            actions.extend(self.handlers["course"].get_available_actions())
        # 假期阶段
        elif is_holiday:
            actions.extend([
                ("1", "旅游", "去外地旅游"),
                ("2", "回家", "回老家探亲"),
                ("3", "娱乐", "在宿舍娱乐"),
                ("4", "学习", "继续学习"),
                ("9", "休息", "好好休息"),
            ])
        # 科研阶段
        else:
            actions.extend(self.handlers["research"].get_available_actions())

        # 毕业论文
        if self.player.year >= 3 and self.player.papers_published >= 1:
            actions.extend(self.handlers["graduation"].get_available_actions())

        # 通用行动
        actions.extend(self.handlers["social"].get_available_actions())
        actions.append(("0", "状态", "查看当前状态"))

        return actions
