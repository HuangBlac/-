"""异变系统 - 处理文本污染和异变效果"""
import random


class MutationSystem:
    """异变系统管理器"""

    def __init__(self):
        # 异变消息
        self.mutation_messages = {
            (0, 0.5): [
                "你感觉一阵不安...",
                "有什么东西在心里躁动...",
                "你隐约听到一些奇怪的声音...",
            ],
            (0.5, 1): [
                "当你睡下，你总感觉到一阵不安...",
                "镜子里的你似乎有点不一样了...",
                "你发现手上出现了奇怪的花纹...",
            ],
            (1, 2): [
                "现实与梦境的边界开始模糊...",
                "你看到的文字开始扭曲变形...",
                "脑海中的声音越来越清晰...",
            ],
            (2, 100): [
                "你已经不属于这个世界了...",
                "是不可名状，还是本就如此？",
                "一切都没有意义了...",
            ]
        }

    def corrupt_text(self, text: str, mutation_level: float) -> str:
        """根据异变程度污染文本

        Args:
            text: 原始文本
            mutation_level: 异变值

        Returns:
            污染后的文本
        """
        if mutation_level <= 0:
            return text

        # 数字替换表（轻度异变）
        digit_map = {
            '0': '〇', '1': '一', '2': '二', '3': '三', '4': '四',
            '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'
        }

        # 严重时用特殊符号
        if mutation_level >= 1:
            digit_map = {
                '0': '☆', '1': '★', '2': '◇', '3': '◆', '4': '○',
                '5': '●', '6': '△', '7': '▲', '8': '□', '9': '■'
            }

        result = text
        for old, new in digit_map.items():
            if random.random() < mutation_level * 0.2:  # 概率替换
                result = result.replace(old, new)

        # 严重异变时插入不可名状的符号
        if mutation_level >= 0.5 and random.random() < mutation_level * 0.3:
            symbols = ["#@%", "&&&", "***", "???", "-%!%!", "~~~"]
            insert_pos = random.randint(0, len(result))
            result = result[:insert_pos] + random.choice(symbols) + result[insert_pos:]

        return result

    def apply_mutation_effect(self, player, log_func) -> bool:
        """应用异变效果

        Args:
            player: 玩家对象
            log_func: 日志记录函数

        Returns:
            是否触发异变信息
        """
        if player.mutation <= 0:
            return False

        # 每轮理智减少 = 异变值 × 5
        sanity_loss = int(player.mutation * 5)
        if sanity_loss > 0:
            player.change_sanity(-sanity_loss)
            log_func(f"【异变侵蚀】你感觉到不可名状的痛苦...理智-{sanity_loss}")

        # 显示异变信息
        for (min_val, max_val), messages in self.mutation_messages.items():
            if min_val <= player.mutation < max_val:
                if random.random() < 0.3:  # 30%概率触发
                    log_func(f"【{player.mutation_level}】{random.choice(messages)}")
                return True

        return False

    def get_corrupted_status_text(self, text: str, mutation_level: float) -> str:
        """获取经过异变处理的文本（可能返回污染版本）

        Args:
            text: 原始文本
            mutation_level: 异变值

        Returns:
            处理后的文本
        """
        if mutation_level > 0 and random.random() < mutation_level * 0.3:
            return self.corrupt_text(text, mutation_level)
        return text
