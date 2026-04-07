"""GUI界面 - 使用tkinter实现图形界面"""
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import List


class GameGUI:
    """游戏图形界面"""

    def __init__(self, game, window_title: str = "克苏鲁研究院"):
        self.game = game
        self.window_title = window_title

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title(window_title)
        self.root.geometry("800x700")
        self.root.configure(bg="#1a1a2e")

        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # 初始化界面
        self._create_widgets()

    def _create_widgets(self):
        """创建界面组件"""
        # ===== 标题区域 =====
        title_frame = tk.Frame(self.root, bg="#16213e", height=50)
        title_frame.pack(fill=tk.X, padx=10, pady=5)

        title_label = tk.Label(
            title_frame,
            text="克苏鲁研究院",
            font=("SimHei", 20, "bold"),
            bg="#16213e",
            fg="#e94560"
        )
        title_label.pack(pady=10)

        # ===== 状态区域 =====
        status_frame = tk.LabelFrame(
            self.root,
            text="当前状态",
            font=("SimHei", 12),
            bg="#1a1a2e",
            fg="#eaeaea"
        )
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_labels = {}
        status_items = [
            ("学期", "semester"),
            ("理智", "sanity"),
            ("行动点", "action_points"),
            ("INT", "INT"),
            ("SEN", "SEN"),
            ("EDU", "EDU"),
            ("STR", "STR"),
            ("SOC", "SOC"),
            ("声望", "reputation"),
            ("研究方向", "direction"),
            ("论文", "papers"),
            ("毕业要求", "grad_req"),
        ]

        # 创建状态标签网格
        for i, (label, key) in enumerate(status_items):
            row, col = i // 4, i % 4
            frame = tk.Frame(status_frame, bg="#1a1a2e")
            frame.grid(row=row, column=col, padx=10, pady=3, sticky="w")

            tk.Label(
                frame,
                text=f"{label}:",
                font=("SimHei", 10),
                bg="#1a1a2e",
                fg="#94a3b8",
                width=8,
                anchor="w"
            ).pack(side=tk.LEFT)

            value_label = tk.Label(
                frame,
                text="--",
                font=("SimHei", 10, "bold"),
                bg="#1a1a2e",
                fg="#ffffff",
                width=10,
                anchor="w"
            )
            value_label.pack(side=tk.LEFT)
            self.status_labels[key] = value_label

        # 导师信息
        advisor_frame = tk.Frame(status_frame, bg="#1a1a2e")
        advisor_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=3, sticky="w")

        tk.Label(
            advisor_frame,
            text="导师:",
            font=("SimHei", 10),
            bg="#1a1a2e",
            fg="#94a3b8",
            width=8,
            anchor="w"
        ).pack(side=tk.LEFT)

        self.advisor_label = tk.Label(
            advisor_frame,
            text="--",
            font=("SimHei", 10, "bold"),
            bg="#1a1a2e",
            fg="#ffffff",
            anchor="w"
        )
        self.advisor_label.pack(side=tk.LEFT)

        # ===== 消息区域 =====
        message_frame = tk.LabelFrame(
            self.root,
            text="游戏日志",
            font=("SimHei", 12),
            bg="#1a1a2e",
            fg="#eaeaea"
        )
        message_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.message_text = scrolledtext.ScrolledText(
            message_frame,
            font=("SimHei", 10),
            bg="#16213e",
            fg="#eaeaea",
            insertbackground="#eaeaea",
            height=15
        )
        self.message_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ===== 行动按钮区域 =====
        action_frame = tk.LabelFrame(
            self.root,
            text="行动",
            font=("SimHei", 12),
            bg="#1a1a2e",
            fg="#eaeaea"
        )
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        self.action_buttons_frame = tk.Frame(action_frame, bg="#1a1a2e")
        self.action_buttons_frame.pack(fill=tk.X, padx=5, pady=5)

        # ===== 输入区域 (用于需要输入的情况) =====
        input_frame = tk.Frame(self.root, bg="#1a1a2e")
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        self.input_entry = tk.Entry(
            input_frame,
            font=("SimHei", 10),
            bg="#16213e",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", lambda e: self._on_input_submit())

        self.submit_btn = tk.Button(
            input_frame,
            text="确认",
            font=("SimHei", 10),
            bg="#e94560",
            fg="#ffffff",
            command=self._on_input_submit,
            relief=tk.FLAT,
            width=10
        )
        self.submit_btn.pack(side=tk.RIGHT)

        # 输入模式标记
        self.input_mode = False
        self.input_callback = None

    def run(self):
        """运行GUI主循环"""
        self.root.mainloop()

    def update_status(self):
        """更新状态显示"""
        status = self.game.player.get_status()
        player = self.game.player

        # 更新各个状态标签
        self.status_labels["semester"].config(
            text=f"{status['学期']} {status['周数']}"
        )

        # 理智值使用原始数值判断颜色
        sanity_value = player.sanity
        sanity_text = f"{sanity_value}/100 ({player.sanity_level})"
        self.status_labels["sanity"].config(
            text=sanity_text,
            fg="#ff6b6b" if sanity_value < 30 else "#4ecdc4"
        )

        # 行动点使用原始数值判断颜色
        ap_value = player.action_points
        self.status_labels["action_points"].config(
            text=f"{ap_value}/{player.max_action_points}",
            fg="#ffd93d" if ap_value > 0 else "#6c757d"
        )
        self.status_labels["INT"].config(text=f"{status['INT直觉']}")
        self.status_labels["SEN"].config(text=f"{status['SEN感知']}")
        self.status_labels["EDU"].config(text=f"{status['EDU知识']}")
        self.status_labels["STR"].config(text=f"{status['STR耐力']}")
        self.status_labels["SOC"].config(text=f"{status['SOC社交']}")
        self.status_labels["reputation"].config(text=f"{player.reputation}")
        self.status_labels["direction"].config(text=f"{status['研究方向']}")
        self.status_labels["papers"].config(
            text=f"{player.papers_published}/{player.graduation_required_papers}"
        )
        self.status_labels["grad_req"].config(text=f"{player.graduation_required_papers}篇")

        # 更新导师信息
        if '导师' in status:
            advisor_text = f"{status['导师']} | 能力:{status['导师能力']} | 性格:{status['导师性格']}"
            self.advisor_label.config(text=advisor_text)

    def update_actions(self):
        """更新行动按钮"""
        # 清除旧按钮
        for widget in self.action_buttons_frame.winfo_children():
            widget.destroy()

        # 获取可用行动
        actions = self.game.get_actions()

        # 创建新按钮
        for action_id, action_name, description in actions:
            btn = tk.Button(
                self.action_buttons_frame,
                text=f"{action_name}",
                font=("SimHei", 10),
                bg="#0f3460",
                fg="#ffffff",
                command=lambda aid=action_id: self.on_action_click(aid),
                relief=tk.FLAT,
                width=12,
                height=1
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)

            # 绑定hover效果
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#e94560"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#0f3460"))

    def show_messages(self, messages: List[str]):
        """显示消息"""
        self.message_text.config(state=tk.NORMAL)
        self.message_text.delete(1.0, tk.END)

        for msg in messages:
            self.message_text.insert(tk.END, msg + "\n")

        self.message_text.see(tk.END)
        self.message_text.config(state=tk.DISABLED)

    def append_messages(self, messages: List[str]):
        """追加消息"""
        self.message_text.config(state=tk.NORMAL)

        for msg in messages:
            self.message_text.insert(tk.END, msg + "\n")

        self.message_text.see(tk.END)
        self.message_text.config(state=tk.DISABLED)

    def clear_messages(self):
        """清空消息"""
        self.message_text.config(state=tk.NORMAL)
        self.message_text.delete(1.0, tk.END)
        self.message_text.config(state=tk.DISABLED)

    def on_action_click(self, action_id: str):
        """处理行动点击"""
        # 清空消息
        self.game.message_log.clear()

        # 执行行动
        should_wait = self.game.do_action(action_id)

        # 显示结果
        if self.game.message_log:
            self.append_messages(self.game.message_log)

        # 更新状态和按钮
        self.update_status()
        self.update_actions()

        # 检查游戏是否结束
        if self.game.game_over:
            self.show_game_over()

    def _on_input_submit(self):
        """处理输入提交"""
        if self.input_mode and self.input_callback:
            text = self.input_entry.get().strip()
            self.input_entry.delete(0, tk.END)
            self.input_callback(text)

    def show_input(self, prompt: str, callback):
        """显示输入框"""
        self.input_mode = True
        self.input_callback = callback
        self.input_entry.focus()

    def hide_input(self):
        """隐藏输入框"""
        self.input_mode = False
        self.input_callback = None

    def show_game_over(self):
        """显示游戏结束"""
        # 禁用所有按钮
        for widget in self.action_buttons_frame.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.DISABLED, bg="#6c757d")

        # 显示结束消息
        self.append_messages(["\n" + "=" * 30])
        self.append_messages(["游戏结束！"])
        self.append_messages(["=" * 30])
