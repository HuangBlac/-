# 克研模拟器

研究生科研生活 + 克苏鲁神话题材的文字冒险/模拟游戏原型。

## 项目介绍

玩家扮演一名进入克苏鲁研究院的研究生，从研一选课、上课和期末考试开始，逐步解锁科研、阅读文献、生成 idea、评估可行性、实验、投稿、毕业论文和答辩流程。

当前项目已经完成一轮状态机化重构：课程、科研、假期、事件选择、调查、社交和毕业论文行动都通过 `game/state_machine.py` 及 `game/states/` 下的状态类组织。Console 模式是主要验收入口。

2026-05-15 项目审查结论：当前版本应视为“Console 主流程可维护原型”，不是 0504 宏观设计的完整实现。下一步优先做 20-30 分钟垂直切片：四种科研方式、路线偏向、导师首次接触和一次异常审稿/调查反馈。

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

2026-05-15 验证结果：

```text
Ran 359 tests
OK
```

2026-06-08 复验结果：

```text
Ran 359 tests
OK
```

复验时仍会输出课程 JSON fallback warning，但测试全部通过。

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
-> 选择目标期刊层级 -> 投稿判定
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
│   ├── journal_system.py         # 五级期刊评分与投稿判定
│   ├── content_generation.py     # Ollama / DeepSeek 内容生成与校验工具
│   ├── states/                   # 课程、科研、假期、毕业、事件输入等状态
│   └── data/                     # 课程、事件、idea、实验方法、期刊、UI 文案等 JSON 数据
├── godot/                        # Godot 4 早期垂直切片原型，尚非主验收入口
├── scripts/                      # 内容生成等辅助脚本
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
- `docs/2026-04-30_论文期刊分层与非常规审稿系统设计.md`：五级期刊评分、投稿判定与非常规审稿事件设计稿。
- `docs/2026-05-04-宏观项目设计文档（灵感整合）.md`：宏观 GDD，包含四路线、材料、二周目和结局蓝图。
- `docs/2026-05-15_项目审查与0504对照.md`：当前实现状态、0504 对照和独立游戏开发视角建议。

## 科研与 idea 数据

- `game/data/ideas.json` 按四个研究方向维护 idea 池：法术与超自然科技分析、神话文本与仪式构造、神明附属种族与独立种族、旧日支配者与外神。
- 每条 idea 数据包含 `name`、`description`、`innovation`，代码运行时再根据玩家属性和创新值生成隐藏可行性。
- 当前科研论文路线只需要 1 个 idea，但该 idea 必须通过实验凑齐 3 个有效成果后才能撰写论文。

## 特别感谢

codex GPT5.3/5.4/5.5，claude code MiniMax2.7，GLM 5.1/5.0/4.7，Kimi 2.5/2.6，qwen-3.6-235B

## TODO: 迁移到 `.env`（待办）

> 索引见 `~/CLAUDE.md` → "API Key 管理与 .env 迁移"。当前 `game/content_generation.py` 走 `os.environ.get(api_key_env)`，默认读 `DEEPSEEK_API_KEY`（可经 `CTHULHU_DEEPSEEK_API_KEY_ENV` 改名）。Console 主流程不调用 LLM；只有内容生成脚本依赖。

- [ ] `pip install python-dotenv`，在 `content_generation.py` 顶部 `load_dotenv()`（或在调用脚本里加）
- [ ] 项目根新建 `.env`（**不入 git**）写 `DEEPSEEK_API_KEY=...`
- [ ] 新建 `.env.example`（占位，可入 git）
- [ ] `.gitignore` 添加 `.env` `.env.*` `!.env.example`
- [ ] 验证：清掉 shell key 后 `python -m unittest discover` 全绿 + `scripts/generate_ollama_content.py` 仍能调通
- [ ] 等所有依赖项目迁移完，再从系统 env 删 `DEEPSEEK_API_KEY`
