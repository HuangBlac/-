"""课程系统"""
import random
from typing import List, Dict
from .character import ResearchDirection


class Course:
    """课程类"""

    def __init__(self, name: str, course_type: str, description: str,
                 skills: Dict[str, int], credits: int = 3):
        self.name = name
        self.course_type = course_type  # "必修" 或 "选修"
        self.description = description
        self.skills = skills  # 技能增益
        self.credits = credits  # 学分
        self.grade = None  # 最终成绩

    def __repr__(self):
        return f"<Course: {self.name} ({self.course_type})>"


# 必修课
REQUIRED_COURSES = [
    Course(
        "拉莱亚语言初步",
        "必修",
        "学习古代克苏鲁语的基础知识",
        {"拉莱亚语言": 3}
    ),
    Course(
        "神话文本阅读",
        "必修",
        "解读克苏鲁神话古籍",
        {"文本解读": 3}
    ),
    Course(
        "形式科学导论",
        "必修",
        "数学、逻辑等形式科学基础",
        {"形式科学": 3}
    ),
]

# 选修课
ELECTIVE_COURSES = [
    Course(
        "法术与召唤法阵",
        "选修",
        "学习绘制召唤法阵的基础知识",
        {"神秘生物学": 2, "说服": 1}
    ),
    Course(
        "旧日支配者认知科学",
        "选修",
        "研究旧日支配者的心智影响",
        {"神话学": 2, "密码学": 1}
    ),
    Course(
        "超自然邪教与混血种族",
        "选修",
        "研究世界各地的神秘教派",
        {"田野调查": 2, "说服": 1}
    ),
    Course(
        "神秘生物学",
        "选修",
        "研究神话生物的生理结构",
        {"神秘生物学": 3}
    ),
]


class CourseSystem:
    """课程管理系统"""

    def __init__(self):
        self.required_courses = REQUIRED_COURSES.copy()
        self.elective_courses = ELECTIVE_COURSES.copy()
        self.selected_electives: List[Course] = []

    def get_course_selection_menu(self) -> str:
        """获取选课菜单"""
        menu = "\n【选修课选课】（选择3门）\n"
        for i, course in enumerate(self.elective_courses, 1):
            menu += f"{i}. {course.name} - {course.description}\n"
            for skill, value in course.skills.items():
                menu += f"   +{value} {skill}\n"
        menu += "\n请输入选修课编号（用空格分隔，如：1 2 3）: "
        return menu

    def select_electives(self, selections: List[int]) -> bool:
        """选择选修课

        Args:
            selections: 选修课编号列表（1-based）

        Returns:
            是否选课成功
        """
        if len(selections) != 3:
            return False

        valid_selections = []
        for s in selections:
            if 1 <= s <= len(self.elective_courses):
                valid_selections.append(s - 1)

        if len(valid_selections) != 3:
            return False

        self.selected_electives = [self.elective_courses[i] for i in valid_selections]
        return True

    def get_all_courses(self) -> List[Course]:
        """获取所有已选课程"""
        return self.required_courses + self.selected_electives

    def take_exam(self, course: Course, ability: int) -> str:
        """参加考试

        Args:
            course: 课程
            ability: 玩家能力值（取各项技能平均值）

        Returns:
            考试结果描述
        """
        # 基础分数 + 随机波动 + 技能加成
        base_score = 60 + random.randint(-10, 15)
        skill_bonus = sum(course.skills.values()) * 2
        score = min(100, base_score + skill_bonus + ability // 10)

        # 成绩等级
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        course.grade = grade
        return f"{course.name}: {score}分 ({grade})"


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
        # 计算平均技能等级
        avg_ability = sum(player.skills.values()) / len(player.skills)

        for course in self.course_system.get_all_courses():
            result = self.course_system.take_exam(course, avg_ability)
            results.append(result)

        self.exams_completed = True
        return "\n".join(results)

    def get_research_direction_from_courses(self) -> ResearchDirection:
        """根据选课决定研究方向

        Returns:
            研究方向
        """
        # 统计选修课类型
        arcane_count = 0  # 法术与超自然科技
        mythos_count = 0  # 神话文本与仪式
        deity_count = 0   # 神明附属种族
        outer_count = 0   # 旧日支配者与外神

        for course in self.course_system.selected_electives:
            if "法术" in course.name or "召唤" in course.name:
                arcane_count += 1
            if "神话文本" in course.name or "邪教" in course.name:
                mythos_count += 1
            if "邪教" in course.name or "混血" in course.name:
                deity_count += 1

        # 根据课程决定方向（选择最高的）
        counts = {
            ResearchDirection.ARCANE_ANALYSIS: arcane_count,
            ResearchDirection.MYTHOS_RITUAL: mythos_count,
            ResearchDirection.DEITY_RACE: deity_count,
            ResearchDirection.OUTER_GOD: outer_count,
        }
        return max(counts, key=counts.get)
