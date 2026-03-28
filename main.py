"""
克苏鲁研究院 (Cthulhu Academy)
研究生模拟游戏 - 主入口
"""

from game.game_engine import GameCore
from ui.console import ConsoleUI


def main():
    """主函数"""
    ui = ConsoleUI()
    ui.clear_screen()
    ui.print_title("克苏鲁研究院")

    # 欢迎界面
    print("""
    欢迎来到克苏鲁研究院！
    这是一所专门研究克苏鲁神话的研究生院。

    你的目标：
    - 在陷入疯狂之前发表足够多的论文
    - 顺利毕业，拿到学位

    警告：接触过多神话知识会损害理智！
    """)

    # 输入玩家名字
    name = input("请输入你的名字: ").strip()
    if not name:
        name = "研究生"

    # 初始化游戏
    game = GameCore(name)
    game.start_game()

    # 游戏主循环
    while not game.game_over:
        # 显示状态
        game.display_status()

        # 显示菜单
        actions = game.get_actions()
        ui.print_menu("行动", actions)

        # 获取输入
        choice = ui.get_input()

        # 清空之前的日志
        game.message_log.clear()

        # 执行行动
        should_wait = game.do_action(choice)

        # 打印行动结果
        if game.message_log:
            print("")
            for msg in game.message_log:
                print(msg)

        # 等待确认（查看状态选项不需要等待）
        if should_wait:
            ui.wait()

    # 游戏结束
    ui.wait()
    print("\n感谢游玩！")


if __name__ == "__main__":
    main()
