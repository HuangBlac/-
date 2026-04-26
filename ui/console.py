"""控制台UI"""
import sys


class ConsoleUI:
    """控制台界面"""

    @staticmethod
    def clear_screen():
        """清屏"""
        print("\n" * 3)

    @staticmethod
    def print_title(title: str):
        """打印标题"""
        print("=" * 50)
        print(f"  {title}")
        print("=" * 50)

    @staticmethod
    def print_menu(title: str, options: list):
        """打印菜单

        Args:
            title: 菜单标题
            options: 选项列表 [(key, name, description), ...]
        """
        print(f"\n【{title}】")
        print("-" * 40)
        for key, name, desc in options:
            print(f"  {key}. {name:<10} - {desc}")
        print("-" * 40)

    @staticmethod
    def get_input(prompt: str = "请选择: ") -> str:
        """获取输入"""
        return input(f"\n{prompt}").strip()

    @staticmethod
    def print_message(message: str, indent: int = 0):
        """打印消息"""
        prefix = "  " * indent
        print(f"{prefix}{message}")

    @staticmethod
    def print_messages(messages: list):
        """打印多条消息"""
        for msg in messages:
            print(f"  {msg}")

    @staticmethod
    def print_separator():
        """打印分隔符"""
        print("-" * 50)

    @staticmethod
    def wait():
        """等待用户确认"""
        input("\n按回车继续...")

    @staticmethod
    def print_status(title: str, data: dict):
        """打印状态信息"""
        print(f"\n【{title}】")
        ConsoleUI.print_separator()
        for key, value in data.items():
            print(f"  {key}: {value}")
        ConsoleUI.print_separator()

    @staticmethod
    def print_lines(lines: list[str]):
        """Print a prepared list of lines."""
        for line in lines:
            print(line)
