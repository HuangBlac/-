"""游戏状态系统 - 检查游戏结束条件"""


class GameStateManager:
    """游戏状态管理器"""

    def __init__(self):
        self.game_over = False
        self.ending = None

    def check_game_over(self, player, graduation_thesis, log_func) -> bool:
        """检查游戏结束条件

        Args:
            player: 玩家对象
            graduation_thesis: 毕业论文系统
            log_func: 日志记录函数

        Returns:
            是否游戏结束
        """
        # 异变值≥2：死亡
        if player.mutation >= 2:
            self.game_over = True
            self.ending = "异变"
            log_func("\n" + "=" * 50)
            log_func("你的异变程度已经无可挽回...")
            log_func("你变成了一个不可名状的怪物")
            log_func(f"最终结局：异变死亡（已发表{player.papers_published}篇论文）")
            log_func("=" * 50)
            return True

        # 理智归零（异变后恢复理智，不再直接结束）
        elif player.sanity <= 0:
            log_func("\n" + "【警告】你的理智彻底耗尽！但你并没有完全疯狂...")
            log_func(f"【异变+1】你的身体开始发生不可名状的变化...")
            log_func(f"当前异变值：{player.mutation:.2f} ({player.mutation_level})")
            log_func("你恢复了部分理智，但异变程度加重了！")
            return False

        # 毕业论文完成
        elif graduation_thesis.passed:
            self.game_over = True
            self.ending = "毕业"
            log_func("\n" + "=" * 50)
            log_func("恭喜！你顺利毕业了！")
            log_func(f"最终结局：获得硕士学位（已发表{player.papers_published}篇论文）")
            log_func("=" * 50)
            return True

        # 超过研三
        elif player.year > 3:
            self.game_over = True
            if player.papers_published >= 1 and graduation_thesis.stage.value != "未开始":
                self.ending = "毕业"
                log_func("\n" + "=" * 50)
                log_func("恭喜！你顺利毕业了！")
                log_func(f"最终结局：获得硕士学位（已发表{player.papers_published}篇论文）")
            else:
                self.ending = "延期"
                log_func("\n" + "=" * 50)
                log_func("你未能完成学业...")
                log_func("请继续努力！")
            log_func("=" * 50)
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
