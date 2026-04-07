"""
克苏鲁研究院 (Cthulhu Academy)
研究生模拟游戏 - GUI版本入口
"""

import tkinter as tk
from tkinter import messagebox
from game.game_engine import GameEngine
from ui.gui import GameGUI


def main():
    """主函数 - GUI版本"""
    # 创建主窗口用于输入名字
    root = tk.Tk()
    root.title("克苏鲁研究院")
    root.geometry("400x200")
    root.configure(bg="#1a1a2e")

    # 居中显示
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 200) // 2
    root.geometry(f"400x200+{x}+{y}")

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
        text="克苏鲁研究院\n现在需要美术设计指导\n游戏玩法也没头绪\n代码也有好多bug\n我完蛋了哈哈\n",
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

    name_entry.bind("<Return>", lambda e: on_start())

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

    # 处理特殊的输入情况
    def handle_course_input(text: str):
        """处理选课输入"""
        game.action_system.awaiting_course_selection = False
        game.message_log.clear()
        result, _ = game.action_system.do_action(text, game.log)
        if result:
            game.log(result)

        gui.append_messages(game.message_log)
        game.message_log.clear()
        gui.update_status()
        gui.update_actions()
        gui.hide_input()

    def handle_idea_input(text: str):
        """处理Idea评估输入"""
        game.message_log.clear()
        game._handle_idea_decision(text)

        gui.append_messages(game.message_log)
        game.message_log.clear()
        gui.update_status()
        gui.update_actions()
        gui.hide_input()

    # 启动GUI主循环
    gui.run()


if __name__ == "__main__":
    main()
