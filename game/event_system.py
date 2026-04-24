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
        base_path = os.path.dirname(os.path.abspath(__file__))
        events_dir = os.path.join(base_path, 'data', 'events')

        # 事件文件映射
        event_files = {
            'random': 'events_random.json',
            'advisor': 'events_advisor.json',
            'advisor_pressure': 'advisor_pressure_event.json',
            'academic': 'events_academic.json',
            'mythos': 'events_mythos.json',
            'social': 'events_social.json',
            'investigation': 'events_investigation.json',
            'holiday': 'events_holiday.json',
            'entertainment': 'events_entertainment.json',
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
            return None

        return random.choice(events)

    def _filter_events(self, events: List[Dict], player) -> List[Dict]:
        """根据玩家状态筛选可用事件"""
        available = []
        for event in events:
            if not self._event_matches_requirements(event, player):
                continue
            if not self._event_matches_trigger(event, player):
                continue

            available.append(event)

        return available

    def _event_matches_requirements(self, event: Dict, player) -> bool:
        """检查 requirement 字段。"""
        req = event.get('requirement')
        if not req:
            return True

        for key, value in req.items():
            player_val = getattr(player, key, 0)

            if isinstance(value, str) and value.startswith(('>=', '>', '<=', '<')):
                op = value[:2] if len(value) > 1 and value[1] in '=<>' else value[0]
                threshold = float(value[len(op):])
                if op == '>=' and player_val < threshold:
                    return False
                if op == '>' and player_val <= threshold:
                    return False
                if op == '<=' and player_val > threshold:
                    return False
                if op == '<' and player_val >= threshold:
                    return False
                continue

            # 向后兼容：数字 requirement 默认表示“至少达到该值”，
            # sanity 继续使用“当前理智不高于阈值”的旧逻辑。
            if key == 'sanity':
                if player.sanity > value:
                    return False
            elif player_val < value:
                return False

        return True

    def _event_matches_trigger(self, event: Dict, player) -> bool:
        """检查 trigger_condition 字段。"""
        trigger = event.get('trigger_condition')
        if trigger in (None, 'always', 'normal', 'random', 'rare', 'periodic', 'weekly'):
            return True

        if trigger == 'low_progress':
            return player.research_progress < 50
        if trigger == 'high_progress':
            return player.research_progress >= 100
        if trigger == 'high_reputation':
            return player.reputation >= 10
        if trigger == 'low_reputation':
            return player.reputation <= 0
        if trigger == 'low_sanity':
            return player.sanity <= 40
        if trigger == 'mutation':
            return player.mutation > 0
        if trigger == 'research':
            return bool(player.research_unlocked and player.research_direction)
        if trigger == 'read':
            return player.research_unlocked
        if trigger == 'submit':
            return bool(player.current_paper or player.papers_published > 0)
        if trigger == 'investigation':
            return True
        if trigger == 'family_pressure':
            return player.SOC < 50

        return False

    def get_advisor_events(self, player) -> List[Dict]:
        """获取导师相关事件"""
        return self.events.get('advisor', [])

    def get_advisor_pressure_events(self, player) -> List[Dict]:
        """获取导师爆压事件。"""
        return self.events.get('advisor_pressure', [])

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

    def has_choices(self, event: Dict) -> bool:
        """事件是否包含选项。"""
        return bool(event.get('choices'))

    def get_choice(self, event: Dict, choice_id: str) -> Optional[Dict]:
        """根据 choice id 获取选项。"""
        for choice in event.get('choices', []):
            if choice['id'] == choice_id:
                return choice
        return None

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

        for attr in ['INT', 'SEN', 'EDU', 'STR', 'SOC']:
            if attr in effect:
                setattr(player, attr, getattr(player, attr) + effect[attr])
                effect_msg.append(f"{attr}{effect[attr]:+d}")

        if 'reputation' in effect:
            player.reputation += effect['reputation']
            effect_msg.append(f"声望{effect['reputation']:+d}")

        if 'progress' in effect:
            player.research_progress = min(255, max(0, player.research_progress + effect['progress']))
            effect_msg.append(f"灵感{effect['progress']:+d}")

        if 'papers_published' in effect:
            player.papers_published += effect['papers_published']
            effect_msg.append(f"论文{effect['papers_published']:+d}")

        if 'mutation' in effect:
            player.mutation += effect['mutation']
            effect_msg.append(f"异变{effect['mutation']:+.2f}")

        return "，".join(effect_msg) if effect_msg else "无"

    def get_followup_event(self, event: Dict, player) -> Optional[Dict]:
        """检查并返回满足条件的后续事件"""
        for followup in event.get('followup', []):
            cond = followup.get('condition', {})
            if 'research_direction' in cond:
                direction = player.research_direction
                if direction is None or direction.name != cond['research_direction']:
                    continue
            return followup
        return None
