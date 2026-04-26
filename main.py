"""
克苏鲁研究院 (Cthulhu Academy)
研究生模拟游戏 - 主入口
"""

def select_mode():
    """选择运行模式"""
    print("\n" + "=" * 50)
    print("  克苏鲁研究院 - 选择运行模式")
    print("=" * 50)
    print("  1. 控制台模式 (命令行)")
    print("  2. GUI模式 (图形界面)")
    print("=" * 50)

    while True:
        choice = input("\n请选择 (1/2): ").strip()
        if choice == "1":
            return "console"
        elif choice == "2":
            return "gui"
        print("请输入 1 或 2")


def main_console():
    """控制台模式主函数"""
    from game.game_engine import GameEngine
    from ui.console import ConsoleUI

    ui = ConsoleUI()
    ui.clear_screen()
    ui.print_title("克苏鲁研究院")

    # 欢迎界面
    print("""
    只有两种人能做科研
    一种是疯子，一种是瞎子
    但是你还是来了……
    """)

    # 输入玩家名字
    name = input("请输入你的名字: ").strip()
    if not name:
        name = "研究生"

    # 初始化游戏
    game = GameEngine(name)
    game.start_game()

    # 游戏主循环
    while not game.game_over:
        # 显示状态
        ui.print_lines(game.get_status_lines())

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
    print("\n游戏没有结束……")


def main_gui():
    """GUI模式主函数"""
    import tkinter as tk
    from game.game_engine import GameEngine
    from ui.gui import GameGUI

    # 创建主窗口用于输入名字
    root = tk.Tk()
    root.title("克苏鲁研究院")
    root.geometry("400x250")
    root.configure(bg="#1a1a2e")

    # 居中显示
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 250) // 2
    root.geometry(f"400x250+{x}+{y}")

    # 标题
    title_label = tk.Label(
        root,
        text="克苏鲁研究院",
        font=("SimHei", 24, "bold"),
        bg="#1a1a2e",
        fg="#e94560"
    )
    title_label.pack(pady=20)

    # 描述
    desc_label = tk.Label(
        root,
        text="只有两种人能做科研\n一种是疯子，一种是瞎子\n但是你还是来了……",
        font=("SimHei", 10),
        bg="#1a1a2e",
        fg="#94a3b8",
        justify=tk.CENTER
    )
    desc_label.pack(pady=10)

    # 输入框
    input_frame = tk.Frame(root, bg="#1a1a2e")
    input_frame.pack(pady=10)

    tk.Label(
        input_frame,
        text="请输入你的名字:",
        font=("SimHei", 11),
        bg="#1a1a2e",
        fg="#ffffff"
    ).pack(side=tk.LEFT, padx=5)

    name_entry = tk.Entry(
        input_frame,
        font=("SimHei", 11),
        width=15
    )
    name_entry.pack(side=tk.LEFT, padx=5)
    name_entry.focus()

    player_name = {"name": None}

    def on_start():
        name = name_entry.get().strip()
        if not name:
            name = "研究生"
        player_name["name"] = name
        root.destroy()

    start_btn = tk.Button(
        root,
        text="开始游戏",
        font=("SimHei", 12, "bold"),
        bg="#e94560",
        fg="#ffffff",
        command=on_start,
        relief=tk.FLAT,
        width=15,
        height=1
    )
    start_btn.pack(pady=15)

    name_entry.bind("<Return>", lambda _: on_start())

    root.mainloop()

    # 检查是否取消
    if player_name["name"] is None:
        return

    player_name_str = player_name["name"]

    # 初始化游戏
    game = GameEngine(player_name_str)
    game.start_game()

    # 创建GUI
    gui = GameGUI(game)

    # 显示初始状态和消息
    gui.update_status()
    gui.update_actions()

    # 显示初始消息
    initial_messages = game.message_log.copy()
    gui.show_messages(initial_messages)

    # 启动GUI主循环
    gui.run()


def main():
    """主函数 - 根据选择运行对应模式"""
    # 选择运行模式
    mode = select_mode()

    if mode == "gui":
        main_gui()
    else:
        main_console()


if __name__ == "__main__":
    main()
