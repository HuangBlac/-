# 克研模拟器

研究生科研生活 + 克苏鲁神话题材的文字冒险/模拟游戏原型。

## 项目介绍

玩家扮演一名进入克苏鲁研究院的研究生，从研一选课、上课和期末考试开始，逐步解锁科研、阅读文献、生成 idea、评估可行性、实验、投稿、毕业论文和答辩流程。

当前项目已经完成一轮状态机化重构：课程、科研、假期、事件选择、调查、社交和毕业论文行动都通过 `game/state_machine.py` 及 `game/states/` 下的状态类组织。Console 模式是主要验收入口。

## 运行

```bash
python main.py
```

启动后选择：

- `1`：控制台模式，当前主要可玩入口。
- `2`：GUI 模式，可启动但自由输入流程仍未完整接入，暂不作为验收入口。

也可以直接启动 GUI 入口：

```bash
python main_gui.py
```

`main_gui.py` 仍保留旧输入回调代码，后续需要和状态机输入流统一。

## 测试

```bash
python -m unittest discover
```

2026-04-29 验证结果：

```text
Ran 45 tests
OK
```

## 当前主流程

```text
研一入学
-> 选课
-> 上课
-> 期末考试
-> 解锁科研
-> 阅读文献
-> 生成 raw idea
-> 评估 idea 可行性
-> 接受 / 打磨 / 丢弃
-> 实验凑齐 3 个有效成果
-> 撰写论文
-> 投稿发表
-> 研三进入毕业论文
-> 开题 / 中期 / 盲审 / 二审 / 答辩
-> 结局判定
```

## 项目结构

```text
CthulhuAcademy/
├── main.py                       # 控制台/GUI 模式选择入口
├── main_gui.py                   # 旧 GUI 直达入口，仍待统一输入流
├── game/
│   ├── game_engine.py            # 系统装配与顶层接口
│   ├── state_machine.py          # 状态机内核
│   ├── state_action_executor.py  # 状态 action 执行编排
│   ├── turn_flow_controller.py   # 行动点、周推进、随机事件、灵感爆发
│   ├── event_flow_controller.py  # 事件选择与事件效果桥接
│   ├── action_menu_provider.py   # 当前菜单聚合
│   ├── states/                   # 课程、科研、假期、毕业、事件输入等状态
│   └── data/                     # 课程、事件、idea、实验方法、UI 文案等 JSON 数据
├── ui/
│   ├── console.py                # 控制台 UI
│   └── gui.py                    # Tkinter GUI
├── tests/                        # unittest 测试
└── docs/                         # 设计、现状、开发日志和问题记录
```

## 文档入口

- `docs/项目现状.md`：当前已落地结构、测试覆盖和边界。
- `docs/成熟想法.md`：已成形、可执行的后续任务。
- `docs/不足汇总.md`：当前仍存在的问题和技术债。
- `docs/2026-04-28_调查碎片与长线探索系统设计.md`：调查碎片、多周目和长线探索系统设计稿。

## 科研与 idea 数据

- `game/data/ideas.json` 按四个研究方向维护 idea 池：法术与超自然科技分析、神话文本与仪式构造、神明附属种族与独立种族、旧日支配者与外神。
- 每条 idea 数据包含 `name`、`description`、`innovation`，代码运行时再根据玩家属性和创新值生成隐藏可行性。
- 当前科研论文路线只需要 1 个 idea，但该 idea 必须通过实验凑齐 3 个有效成果后才能撰写论文。

## 特别感谢

codex GPT5.3/5.4/5.5，claude code MiniMax2.7，GLM 5.1/5.0/4.7，Kimi 2.5/2.6，qwen-3.6-235B
