"""事件系统"""
import random


class EventSystem:
    """事件管理器"""

    def __init__(self):
        self.events = self._init_events()

    def _init_events(self) -> list:
        """初始化事件库"""
        return [
            {
                "id": 1,
                "title": "奇怪的梦",
                "description": "你最近总是做奇怪的梦，梦中有一个巨大的章鱼头怪物在呼唤你。",
                "type": "mythos",
                "effect": {"sanity": -5, "inspiration": 2},
                "requirement": None,
            },
            {
                "id": 2,
                "title": "图书馆禁书",
                "description": "你在图书馆的角落里发现了一本没有被编目的古籍。",
                "type": "mythos",
                "effect": {"sanity": -10, "knowledge": 3},
                "requirement": None,
            },
            {
                "id": 3,
                "title": "导师的暗示",
                "description": "导师在组会上暗示你，有些知识是'不应该被知道的'。",
                "type": "academic",
                "effect": {"sanity": -3, "reputation": 1},
                "requirement": None,
            },
            {
                "id": 4,
                "title": "同门的警告",
                "description": "张同学悄悄告诉你，他最近看到了'不该看的东西'。",
                "type": "social",
                "effect": {"sanity": -5, "inspiration": 1},
                "requirement": None,
            },
            {
                "id": 5,
                "title": "实验室意外",
                "description": "你的实验结果出现了无法解释的异常数据。",
                "type": "academic",
                "effect": {"knowledge": 2, "sanity": -8},
                "requirement": None,
            },
            {
                "id": 6,
                "title": "神秘符号",
                "description": "你在校园墙上看到了一个奇怪的符号，似乎在哪里见过...",
                "type": "mythos",
                "effect": {"inspiration": 3, "sanity": -5},
                "requirement": None,
            },
            {
                "id": 7,
                "title": "评审的邀请",
                "description": "深潜者评审邀请你参与一个'特别的研究项目'。",
                "type": "academic",
                "effect": {"reputation": 5, "sanity": -10},
                "requirement": {"reputation": 10},
            },
            {
                "id": 8,
                "title": "失踪的同学",
                "description": "李同学已经一周没来上课了，有人说看到他深夜走进了森林...",
                "type": "mythos",
                "effect": {"sanity": -15, "inspiration": 5},
                "requirement": None,
            },
            {
                "id": 9,
                "title": "论文被引用",
                "description": "你的论文被一篇奇怪的期刊引用了，作者署名是一串无法读出的符号。",
                "type": "academic",
                "effect": {"reputation": 3},
                "requirement": {"papers_published": 1},
            },
            {
                "id": 10,
                "title": "直视深渊",
                "description": "你似乎看到了世界的真实面貌...那是一个充满疯狂与混沌的深渊。",
                "type": "mythos",
                "effect": {"sanity": -20, "knowledge": 5},
                "requirement": {"knowledge": 15},
            },
        ]

    def get_random_event(self, is_holiday: bool = False) -> dict:
        """获取随机事件

        Args:
            is_holiday: 是否在假期（暑假/寒假）
        """
        if is_holiday:
            # 假期事件池：主要是正面或中性事件
            holiday_events = [e for e in self.events if e.get("effect", {}).get("sanity", 0) >= 0]
            if holiday_events:
                return random.choice(holiday_events)
        return random.choice(self.events)

    def get_events_by_type(self, event_type: str) -> list:
        """按类型获取事件"""
        return [e for e in self.events if e["type"] == event_type]

    def get_available_events(self, player) -> list:
        """获取满足条件的事件"""
        available = []
        for event in self.events:
            req = event.get("requirement")
            if req is None:
                available.append(event)
            else:
                # 检查条件
                valid = True
                if "reputation" in req and player.reputation < req["reputation"]:
                    valid = False
                if "knowledge" in req and player.knowledge < req["knowledge"]:
                    valid = False
                if "papers_published" in req and player.papers_published < req["papers_published"]:
                    valid = False
                if valid:
                    available.append(event)
        return available
