"""游戏状态系统 - 检查游戏结束条件"""
import json
import os


class GameStateManager:
    """游戏状态管理器"""

    def __init__(self):
        self.game_over = False
        self.ending = None
        self.endings_data = self._load_endings()

    def _load_endings(self) -> dict:
        """加载结局文本"""
        endings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'endings.json')
        try:
            with open(endings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"endings": {}}

    def _print_ending(self, key: str, player, log_func):
        """打印结局文本"""
        endings = self.endings_data.get("endings", {})
        ending = endings.get(key, {})
        lines = ending.get("description", [])
        title = ending.get("title", key)

        log_func("\n" + "=" * 50)
        log_func(f"【结局：{title}】")
        for line in lines:
            log_func(line.format(
                papers_published=player.papers_published,
                sanity=player.sanity,
                mutation=player.mutation,
            ))
        log_func("=" * 50)

    def check_game_over(self, player, graduation_thesis, log_func) -> bool:
        """检查游戏结束条件"""
        # 异变值≥2：死亡
        if player.mutation >= 2:
            self.game_over = True
            self.ending = "异变"
            self._print_ending("mutation", player, log_func)
            return True

        # 理智归零：触发异变，不直接结束
        elif player.sanity <= 0:
            log_func("\n【警告】你的理智彻底耗尽！但你并没有完全疯狂...")
            log_func(f"【异变+1】你的身体开始发生不可名状的变化...")
            log_func(f"当前异变值：{player.mutation:.2f} ({player.mutation_level})")
            log_func("你恢复了部分理智，但异变程度加重了！")
            return False

        # 毕业论文完成
        elif graduation_thesis.passed:
            self.game_over = True
            self.ending = "毕业"
            # 根据状态选择结局变体
            if player.mutation >= 1:
                self._print_ending("graduation_high_mutation", player, log_func)
            elif player.sanity < 30:
                self._print_ending("graduation_low_sanity", player, log_func)
            else:
                self._print_ending("graduation_normal", player, log_func)
            return True

        # 超过研三
        elif player.year > 3:
            self.game_over = True
            if player.papers_published >= 1 and graduation_thesis.stage.value != "未开始":
                self.ending = "毕业"
                if player.mutation >= 1:
                    self._print_ending("graduation_high_mutation", player, log_func)
                elif player.sanity < 30:
                    self._print_ending("graduation_low_sanity", player, log_func)
                else:
                    self._print_ending("graduation_normal", player, log_func)
            else:
                self.ending = "延期"
                self._print_ending("延期", player, log_func)
            return True

        return False

    def is_ended(self) -> bool:
        """检查游戏是否已结束"""
        return self.game_over

    def get_ending(self):
        """获取结局类型"""
        return self.ending

    def reset(self):
        """重置游戏状态"""
        self.game_over = False
        self.ending = None
