"""事件系统 - 从JSON文件加载事件"""
import random
import json
import os
from typing import List, Dict, Optional


class EventSystem:
    """事件管理器 - 从JSON文件加载事件"""

    def __init__(self):
        self.events: Dict[str, List[Dict]] = {}
        self._load_events()

    def _load_events(self):
        """从JSON文件加载事件"""
        # 获取data/events目录路径
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        events_dir = os.path.join(base_path, 'data', 'events')

        # 事件文件映射
        event_files = {
            'random': 'events_random.json',
            'advisor': 'events_advisor.json',
            'academic': 'events_academic.json',
            'mythos': 'events_mythos.json',
            'social': 'events_social.json',
            'investigation': 'events_investigation.json',
            'holiday': 'events_holiday.json',
        }

        for event_type, filename in event_files.items():
            filepath = os.path.join(events_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.events[event_type] = data.get('events', [])
            except FileNotFoundError:
                print(f"警告: 事件文件 {filepath} 未找到")
                self.events[event_type] = []
            except json.JSONDecodeError:
                print(f"警告: 事件文件 {filepath} 解析失败")
                self.events[event_type] = []

    def get_events(self, event_type: str) -> List[Dict]:
        """获取指定类型的事件列表"""
        return self.events.get(event_type, [])

    def get_random_event(self, event_type: str = 'random', player=None) -> Optional[Dict]:
        """获取随机事件

        Args:
            event_type: 事件类型
            player: 玩家对象（用于条件筛选）

        Returns:
            随机事件字典
        """
        events = self.events.get(event_type, [])
        if not events:
            return None

        # 如果提供了玩家，筛选满足条件的事件
        if player:
            available = self._filter_events(events, player)
            if available:
                return random.choice(available)

        return random.choice(events)

    def _filter_events(self, events: List[Dict], player) -> List[Dict]:
        """根据玩家状态筛选可用事件"""
        available = []
        for event in events:
            # 检查是否有触发条件
            trigger = event.get('trigger_condition')

            # 检查requirements
            req = event.get('requirement')
            if req:
                if 'reputation' in req and player.reputation < req['reputation']:
                    continue
                if 'knowledge' in req and player.knowledge < req['knowledge']:
                    continue
                if 'papers_published' in req and player.papers_published < req['papers_published']:
                    continue
                if 'sanity' in req and player.sanity > req['sanity']:  # sanity条件是小于等于
                    continue

            # 根据导师状态筛选
            if player.advisor:
                # 爆压事件
                if trigger == 'high_pressure' and player.advisor.personality_value < 61:
                    continue
                if trigger == 'extreme' and player.advisor.personality_value < 90:
                    continue
                if trigger == 'nyarlathotep' and not player.advisor.is_nyarrothotep:
                    continue
                if trigger == 'has_assistant' and not player.advisor.has_assistant:
                    continue
                if trigger == 'low_ability' and not player.advisor.requires_lateral_work:
                    continue
                if trigger == 'high_ability' and player.advisor.ability_value <= 60:
                    continue

            available.append(event)

        return available

    def get_advisor_events(self, player) -> List[Dict]:
        """获取导师相关事件"""
        return self._filter_events(self.events.get('advisor', []), player)

    def get_academic_events(self, player) -> List[Dict]:
        """获取学术事件"""
        return self._filter_events(self.events.get('academic', []), player)

    def get_mythos_events(self, player) -> List[Dict]:
        """获取神话事件"""
        return self._filter_events(self.events.get('mythos', []), player)

    def get_social_events(self, player) -> List[Dict]:
        """获取社交事件"""
        return self._filter_events(self.events.get('social', []), player)

    def get_investigation_events(self, player) -> List[Dict]:
        """获取调查事件"""
        return self._filter_events(self.events.get('investigation', []), player)

    def get_holiday_events(self, player) -> List[Dict]:
        """获取假期事件"""
        return self._filter_events(self.events.get('holiday', []), player)

    def apply_event_effect(self, player, event: Dict, choice_id: str = None) -> str:
        """应用事件效果

        Args:
            player: 玩家对象
            event: 事件字典
            choice_id: 选择的选项ID（如果有choices）

        Returns:
            效果描述
        """
        effect_msg = []

        # 检查是否有choices
        if 'choices' in event and choice_id:
            for choice in event['choices']:
                if choice['id'] == choice_id:
                    effect = choice.get('effect', {})
                    break
            else:
                effect = {}
        else:
            effect = event.get('effect', {})

        # 应用各项效果
        if 'sanity' in effect:
            player.change_sanity(effect['sanity'])
            effect_msg.append(f"理智{effect['sanity']:+d}")

        if 'knowledge' in effect:
            player.knowledge += effect['knowledge']
            effect_msg.append(f"知识{effect['knowledge']:+d}")

        if 'inspiration' in effect:
            player.inspiration += effect['inspiration']
            effect_msg.append(f"灵感{effect['inspiration']:+d}")

        if 'reputation' in effect:
            player.reputation += effect['reputation']
            effect_msg.append(f"声望{effect['reputation']:+d}")

        if 'progress' in effect:
            player.research_progress += effect['progress']
            effect_msg.append(f"研究进度{effect['progress']:+d}")

        if 'papers_published' in effect:
            player.papers_published += effect['papers_published']
            effect_msg.append(f"论文{effect['papers_published']:+d}")

        if 'mutation' in effect:
            player.mutation += effect['mutation']
            effect_msg.append(f"异变{effect['mutation']:+.2f}")

        return "，".join(effect_msg) if effect_msg else "无"
