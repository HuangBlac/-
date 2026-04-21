"""课程系统 - 从JSON加载课程数据"""
import random
import json
import os
from typing import List, Dict
from .character import ResearchDirection, ability_check, CheckResult


class Course:
    """课程类"""

    def __init__(self, name: str, course_type: str, description: str,
                 attributes: Dict[str, int], credits: int = 3, hidden: bool = False):
        self.name = name
        self.course_type = course_type  # "必修" 或 "选修"
        self.description = description
        self.attributes = attributes  # 新属性加成 {INT: 2, SEN: 3}
        self.credits = credits  # 学分
        self.grade = None  # 最终成绩
        self.study_count = 0  # 学习次数
        self.hidden = hidden  # 是否隐藏（如奈亚课程）
        self.passed = False  # 是否已通过

    def __repr__(self):
        return f"<Course: {self.name} ({self.course_type})>"


def load_courses_from_json() -> tuple:
    """从JSON文件加载课程数据

    Returns:
        (required_courses, elective_courses, hidden_courses)
    """
    # 获取data目录路径
    base_path = os.path.dirname(os.path.abspath(__file__))
    courses_file = os.path.join(base_path, 'data', 'courses.json')

    try:
        with open(courses_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 加载必修课
        required_courses = []
        for c in data.get('required_courses', []):
            course = Course(
                name=c['name'],
                course_type=c['type'],
                description=c['description'],
                attributes=c.get('attributes', {}),
                credits=c.get('credits', 3),
                hidden=c.get('hidden', False)
            )
            required_courses.append(course)

        # 加载选修课
        elective_courses = []
        for c in data.get('elective_courses', []):
            course = Course(
                name=c['name'],
                course_type=c['type'],
                description=c['description'],
                attributes=c.get('attributes', {}),
                credits=c.get('credits', 3),
                hidden=c.get('hidden', False)
            )
            elective_courses.append(course)

        # 加载隐藏课程
        hidden_courses = []
        for c in data.get('hidden_courses', []):
            course = Course(
                name=c['name'],
                course_type=c['type'],
                description=c['description'],
                attributes=c.get('attributes', {}),
                credits=c.get('credits', 3),
                hidden=c.get('hidden', True)
            )
            hidden_courses.append(course)

        return required_courses, elective_courses, hidden_courses

    except FileNotFoundError:
        print(f"警告: 课程文件 {courses_file} 未找到，使用默认课程")
        return _get_default_courses()
    except json.JSONDecodeError:
        print(f"警告: 课程文件 {courses_file} 解析失败，使用默认课程")
        return _get_default_courses()


def _get_default_courses() -> tuple:
    """获取默认课程（当JSON加载失败时使用）"""
    required = [
        Course("拉莱亚语言初步", "必修", "学习古代克苏鲁语的基础知识", {"EDU": 2, "SEN": 1}),
        Course("神话文本阅读", "必修", "解读克苏鲁神话古籍", {"EDU": 2, "SEN": 2}),
        Course("形式科学导论", "必修", "数学、逻辑等形式科学基础", {"EDU": 2, "INT": 2}),
    ]
    elective = [
        Course("法术与召唤法阵", "选修", "学习绘制召唤法阵的基础知识", {"INT": 2, "SEN": 1}),
        Course("低理智生存技巧", "选修", "教授在理智值较低时的生存技能", {"STR": 3}),
        Course("旧日支配者认知科学", "选修", "研究旧日支配者的心智影响", {"INT": 2, "SEN": 1}),
        Course("混血种族研究", "选修", "研究世界各地的神秘教派和混血种族", {"SEN": 2, "SOC": 1}),
        Course("神秘生物学", "选修", "研究神话生物的生理结构", {"SEN": 3}),
        Course("邪教信徒心理剖析", "选修", "分析邪教信徒的心理动机和行为模式", {"SOC": 2, "INT": 1}),
        Course("高级拉莱亚文本", "选修", "发表外星论文的必修内容", {"EDU": 2, "SEN": 1}),
        Course("深度学习与克苏鲁", "选修", "用一个不可名状的内容描述更不可名状的内容", {"INT": 2, "EDU": 1}),
    ]
    hidden = [
        Course("奈亚子伟大", "隐藏", "由奈亚提亚普导师亲自授课的终极课程", {"INT": 5, "SEN": 5, "EDU": 5}, hidden=True),
    ]
    return required, elective, hidden


# 从JSON加载课程数据
REQUIRED_COURSES, ELECTIVE_COURSES, HIDDEN_ELECTIVE_COURSES = load_courses_from_json()


class CourseSystem:
    """课程管理系统"""

    def __init__(self):
        self.required_courses = [Course(c.name, c.course_type, c.description,
                                         dict(c.attributes), c.credits) for c in REQUIRED_COURSES]
        self.elective_courses = [Course(c.name, c.course_type, c.description,
                                          dict(c.attributes), c.credits) for c in ELECTIVE_COURSES]
        self.hidden_courses = [Course(c.name, c.course_type, c.description,
                                       dict(c.attributes), c.credits, c.hidden) for c in HIDDEN_ELECTIVE_COURSES]
        self.selected_electives: List[Course] = []
        self.first_semester_completed = False  # 第一学期是否完成

    def get_available_electives(self) -> List[Course]:
        """获取可选的选修课（排除隐藏课程）"""
        return [c for c in self.elective_courses if not c.hidden]

    def get_course_selection_menu(self) -> str:
        """获取选课菜单"""
        menu = "\n【选修课选课】（选择3门）\n"
        for i, course in enumerate(self.get_available_electives(), 1):
            menu += f"{i}. {course.name} - {course.description}\n"
            for attr, value in course.attributes.items():
                menu += f"   +{value} {attr}\n"
        menu += "\n请输入选修课编号（用空格分隔，如：1 2 3）: "
        return menu

    def select_electives(self, selections: List[int]) -> bool:
        """选择选修课

        Args:
            selections: 选修课编号列表（1-based）

        Returns:
            是否选课成功
        """
        available = self.get_available_electives()
        if len(selections) != 3:
            return False

        valid_selections = []
        for s in selections:
            if 1 <= s <= len(available):
                valid_selections.append(s - 1)

        if len(valid_selections) != 3:
            return False

        self.selected_electives = [available[i] for i in valid_selections]
        return True

    def get_all_courses(self) -> List[Course]:
        """获取所有已选课程"""
        return self.required_courses + self.selected_electives

    def get_active_courses(self) -> List[Course]:
        """获取当前需要上的课程（排除已通过的）"""
        active = []

        # 必修课：未通过的都需要上
        for course in self.required_courses:
            if not course.passed:
                active.append(course)

        # 选修课：只在第一学期上
        if not self.first_semester_completed:
            active.extend(self.selected_electives)

        return active

    def take_exam(self, course: Course, player) -> str:
        """参加考试（使用新判定系统）

        判定：1d100 < EDU + 学习次数×20
        1=大成功：满分100
        大成功：直接通过，属性+1d6
        成功：正常通过，属性+1d4
        失败：需要补考
        大失败：理智损失

        Args:
            course: 课程
            player: 玩家对象

        Returns:
            考试结果描述
        """
        # 判定阈值 = EDU + 学习次数×20
        difficulty = player.EDU + course.study_count * 20

        # 进行判定
        check_result, roll = ability_check(player, "EDU", difficulty)

        result_msg = [f"【{course.name}】判定: {check_result} (骰点:{roll} vs 阈值:{difficulty})"]

        if check_result == CheckResult.CRITICAL_SUCCESS:
            # 大成功：满分100
            score = 100
            grade = "A+"
            course.passed = True

            # 属性加成：INT/SEN/EDU/STR +1d6（不含SOC）
            for attr in ["INT", "SEN", "EDU", "STR"]:
                if attr in course.attributes:
                    bonus = random.randint(1, 6)
                    current = getattr(player, attr)
                    setattr(player, attr, current + bonus)
                    result_msg.append(f"{attr}+{bonus}")

            result_msg.append("【满分】你获得了满分！所有属性大幅提升！")

        elif check_result in [CheckResult.EXTREME_SUCCESS, CheckResult.HARD_SUCCESS, CheckResult.SUCCESS]:
            # 成功：通过
            score = random.randint(70, 95)
            if score >= 90:
                grade = "A"
            elif score >= 80:
                grade = "B"
            elif score >= 70:
                grade = "C"
            else:
                grade = "D"

            course.passed = True

            # 属性加成：INT/SEN/EDU/STR +1d4
            for attr in ["INT", "SEN", "EDU", "STR"]:
                if attr in course.attributes:
                    bonus = random.randint(1, 4)
                    current = getattr(player, attr)
                    setattr(player, attr, current + bonus)
                    result_msg.append(f"{attr}+{bonus}")

            result_msg.append(f"【通过】成绩: {score}分 ({grade})")

        elif check_result == CheckResult.FAILURE:
            # 失败：需要补考
            grade = "F"
            score = random.randint(40, 59)
            result_msg.append(f"【未通过】成绩: {score}分 ({grade})")
            result_msg.append("需要在下学期补考。")

        else:
            # 大失败：理智损失
            grade = "F"
            score = random.randint(20, 39)
            san_loss = random.randint(10, 20)
            player.change_sanity(-san_loss)
            result_msg.append(f"【大失败】成绩: {score}分 ({grade})")
            result_msg.append(f"你的精神受到了冲击...理智-{san_loss}")

        course.grade = grade
        return "\n".join(result_msg)


class ExamSystem:
    """考试系统"""

    def __init__(self, course_system: CourseSystem):
        self.course_system = course_system
        self.exams_completed = False

    def hold_final_exams(self, player) -> str:
        """举行期末考试

        Args:
            player: 玩家对象

        Returns:
            考试结果
        """
        results = []

        # 获取当前需要考试的课程
        active_courses = self.course_system.get_active_courses()

        for course in active_courses:
            course.study_count += 1  # 增加学习次数
            result = self.course_system.take_exam(course, player)
            results.append(result)

        # 检查是否完成第一学期
        all_passed = all(c.passed for c in active_courses)
        if all_passed:
            self.course_system.first_semester_completed = True
            player.research_unlocked = True
            results.append("\n【第一学期已完成】你可以进入科研阶段了！")

        self.exams_completed = True
        return "\n".join(results)

    def get_research_direction_from_courses(self) -> ResearchDirection:
        """根据选课决定研究方向

        Returns:
            研究方向
        """
        # 统计选修课类型
        arcane_count = 0    # 法术与超自然科技分析
        mythos_count = 0    # 神话文本与仪式构造
        deity_count = 0     # 神明附属种族与独立种族
        outer_count = 0     # 旧日支配者与外神

        for course in self.course_system.selected_electives:
            if "法术" in course.name or "召唤" in course.name:
                arcane_count += 2
            if "旧日支配者" in course.name or "认知" in course.name:
                outer_count += 2
            if "混血" in course.name or "邪教" in course.name:
                deity_count += 2
            if "神秘生物" in course.name:
                deity_count += 1

        counts = {
            ResearchDirection.ARCANE_ANALYSIS: arcane_count,
            ResearchDirection.MYTHOS_RITUAL: mythos_count,
            ResearchDirection.DEITY_RACE: deity_count,
            ResearchDirection.OUTER_GOD: outer_count,
        }

        max_score = max(counts.values())

        if max_score == 0:
            return random.choice(list(ResearchDirection))

        return max(counts, key=counts.get)
