# 论文期刊分层与非常规审稿系统

## 1. Overview

将当前单一的"接受/拒稿"投稿判定，扩展为由 idea 创新、实验数量与质量、学术声望共同决定的五级期刊系统。玩家主动选择目标期刊层级，系统按综合分数判定直接接受、小修后接受、降档接受、大修、拒稿或 Desk Reject。高层级发表更容易触发超凡审稿和真相认知事件，把学术成就与克苏鲁真相认知连接起来。

## 2. Player Fantasy

玩家是一名在克苏鲁研究院求学的研究生，希望自己的科研成果发表在更好的期刊上以获得声望、顺利毕业。但随着论文层级提升，审稿流程逐渐接触到超凡生命、不可名状读者或旧日支配者的间接视线。玩家要在"稳妥发表保毕业"和"冒险冲顶刊触真相"之间做出抉择，感受到学术追求背后逐渐揭开的宇宙恐怖。

## 3. Detailed Rules

### 3.1 五级期刊层级

| 层级 ID | 叙事定位 | 现实映射 | 核心风险 |
|---------|----------|----------|----------|
| `top` | 研究院真正关注的禁忌成果 | Nature/Science/顶会级 | 超凡生命、旧日审稿概率最高 |
| `disciplinary` | 方向内公认突破 | 领域顶刊/顶会 | 容易暴露研究中的异常真相 |
| `good` | 正经成果 | 主流优质期刊 | 学术压力明显，有少量异常审稿 |
| `water` | 可毕业的低质量发表 | 普通可发期刊 | 学术收益低，异常概率低 |
| `school` | 校内/院内兜底发表 | 学报/内部刊物 | 基本安全，但声望收益很低 |

### 3.2 投稿前评分

投稿前计算三个归一化到 `0-100` 的分数：

- **创新分 (`innovation_score`)**：由论文绑定 idea 的平均创新值决定
- **实验分 (`experiment_score`)**：由实验成果的数量、质量、三维平衡度决定
- **声望分 (`reputation_score`)**：由已发表论文积累、导师水平、过往社交经历决定

综合分 `tier_score = innovation_score * 0.42 + experiment_score * 0.38 + reputation_score * 0.20`

### 3.3 目标期刊选择与判定

玩家在 `research.phase` 选择"投稿"后，进入 `research.submission_target` 状态：

1. 系统展示当前论文的三维评分和综合分
2. 玩家选择目标期刊层级
3. 系统检查硬门槛（创新门槛、实验门槛、声望门槛）
4. 若硬门槛满足，计算 `review_score = tier_score + social_review_bonus + review_roll`
5. 根据 `score_gap = review_score - target_threshold` 判定结果

判定结果：

| 条件 | 结果 |
|------|------|
| 硬门槛不满足，且低于目标门槛 >= 15 | Desk Reject |
| score_gap >= 10 | 直接接受 |
| 0 <= score_gap < 10 | 小修后接受 |
| -10 <= score_gap < 0 | 降档接受 |
| -20 <= score_gap < -10 | 大修 |
| score_gap < -20 | 拒稿 |

降档规则：顶刊 -> 学科顶刊 -> 优秀期刊 -> 水刊 -> 学报 -> 拒稿

### 3.4 发表收益

发表后获得声望收益和理智恢复，收益随层级提升而增加。所有收益展示格式为：

```
发表论文+1（顶刊）
声望 +38（累计 74）
理智 +12
```

### 3.5 非常规审稿事件

发表层级越高，越容易触发非常规事件。触发后通过 `EventFlowController` 推入 `input.event_choice` 状态。

事件类型：非人审稿人、超凡生命通信、旧日审稿、反常引用链、学术现实打击。

## 4. Formulas

### 4.1 创新分

```
avg_innovation = sum(idea.innovation for idea in paper.ideas) / len(paper.ideas)
innovation_score = clamp(round(avg_innovation * 10), 0, 100)
```

创新门槛（目标期刊要求）：

| 层级 | min_innovation |
|------|----------------|
| top | 9 |
| disciplinary | 8 |
| good | 6 |
| water | 4 |
| school | 无 |

### 4.2 实验分

```
result_power = theory + experiment + depth
valid_result = result_power >= 3
strong_result = result_power >= 9
breakthrough_result = result_power >= 12

valid_count = count(valid_result)
avg_result_power = sum(result_power for valid_result) / max(1, valid_count)

quantity_score = clamp(24 + (valid_count - 3) * 8, 0, 40)
quality_score = clamp(round(avg_result_power / 15 * 60), 0, 60)
balance_bonus = 5 if min(total_theory, total_experiment, total_depth) >= valid_count * 2 else 0

experiment_score = clamp(quantity_score + quality_score + balance_bonus, 0, 100)
```

### 4.3 声望分

```
paper_reputation = clamp(player.reputation, 0, 80)

advisor_bonus =
  -5 if no advisor
   0 if advisor.ability_value <= 40
   5 if 41 <= advisor.ability_value <= 60
  10 if 61 <= advisor.ability_value <= 80
  15 if 81 <= advisor.ability_value <= 94
  20 if advisor.ability_value >= 95
  25 if advisor.is_nyarrothotep

social_bonus = clamp(successful_social_events * 2 + academic_network_level * 5, 0, 25)
reputation_score = clamp(paper_reputation + advisor_bonus + social_bonus, 0, 100)
```

> 社交系统尚未完善时，`successful_social_events` 和 `academic_network_level` 默认为 0。

### 4.4 综合分

```
tier_score = round(innovation_score * 0.42 + experiment_score * 0.38 + reputation_score * 0.20)
```

### 4.5 投稿判定

```
target_threshold = journal_tier[target].tier_score_threshold
target_hard_requirements_met = 创新门槛 and 实验门槛 and (声望门槛 or 无门槛)

social_review_bonus = round(((SOC + EDU) // 2 - 55) * 0.25)
review_roll = random.randint(-10, 10)
review_score = tier_score + social_review_bonus + review_roll
score_gap = review_score - target_threshold
```

### 4.6 非常规事件触发概率

```
base_anomaly_chance = journal_tier[tier].base_anomaly_chance
innovation_bonus = 0.05 if avg_innovation >= 9 else 0
outer_god_bonus = 0.05 if any(idea.direction == OUTER_GOD) else 0
mutation_bonus = min(0.10, player.mutation * 0.05)
advisor_bonus = 0.08 if advisor.is_eldritch else 0

anomaly_chance = clamp(base_anomaly_chance + innovation_bonus + outer_god_bonus + mutation_bonus + advisor_bonus, 0, 0.45)
```

### 4.7 真相认知

```
truth_gain = {非人审稿人: 3, 超凡生命通信: 6, 旧日审稿: 10, 反常引用链: 4, 学术现实打击: 0}
mutation_gain = round(truth_gain * 0.01, 2)
```

## 5. Edge Cases

### 5.1 论文 tier_score < 30
- 不应允许投稿
- 提示"论文尚不足以形成可发表成果"，保留当前论文并要求继续写作或补实验

### 5.2 降档后学报仍不满足
- 学报降档直接变为拒稿
- 不触发降档链的无限循环

### 5.3 异常事件触发时论文已清空
- 异常事件在论文成功发表后触发
- 判定结果已保存，事件效果不影响已发表的记录

### 5.4 社交系统尚未完善
- `social_bonus` 兼容为 0
- 后续社交系统接入时自动生效

### 5.5 无导师情况
- `advisor_bonus = -5`
- 导师相关事件效果不触发

## 6. Dependencies

| 依赖系统 | 用途 |
|----------|------|
| `Player` | 属性读取、声望/异变/理智修改、论文计数 |
| `ResearchSystem` | 当前论文获取、idea 和实验结果数据 |
| `Paper` | 论文统计数据（创新值、实验三维） |
| `EventFlowController` | 异常事件推入 `input.event_choice` |
| `EventSystem` | 事件效果应用 |
| `StateMachine` | 新增 `research.submission_target` 状态（判定结果通过 `pop_state` 携带文本回到 `research.phase`，未引入独立 `research.review_result`） |
| `AdvisorSystem` | 导师属性读取（能力值、是否为超凡生物） |

## 7. Tuning Knobs

所有以下数值配置在 `game/data/journal_tiers.json`：

| 配置项 | 当前值 | 调优方向 |
|--------|--------|----------|
| 顶刊 tier_score_threshold | 88 | 提高以增加顶刊难度 |
| 顶刊 min_experiment_score | 82 | 配合实验系统迭代调整 |
| 顶刊 base_anomaly_chance | 0.25 | 控制恐怖氛围浓度 |
| 创新分权重 | 0.42 | 可微调以改变创新 vs 实验的相对重要性 |
| 实验分权重 | 0.38 | 同上 |
| 声望分权重 | 0.20 | 同上 |
| 数量分上限 | 40 | 控制堆实验的收益上限 |
| 质量分上限 | 60 | 控制实验质量的重要性 |

所有异常事件配置在 `game/data/review_anomaly_events.json`：

| 配置项 | 说明 |
|--------|------|
| weight | 事件权重，可调整稀有度 |
| sanity_min/max | 理智影响范围 |
| mutation_min/max | 异变影响范围 |
| truth_gain | 真相认知值 |

## 8. Acceptance Criteria

### 8.1 数据层
- [x] `game/data/journal_tiers.json` 可被 `json.load` 正常解析
- [x] `game/data/review_anomaly_events.json` 可被 `json.load` 正常解析
- [x] 两个 JSON 均有基本的 schema 验证测试（`test_journal_system.py` 中 7 个 schema 测试覆盖必填字段、阈值递减、权重和=1、事件 ID 唯一）

### 8.2 评分层
- [x] `calculate_innovation_score` 对已知输入返回预期值（单元测试）
- [x] `calculate_experiment_score` 对已知输入返回预期值（单元测试）
- [x] `calculate_reputation_score` 对已知输入返回预期值（单元测试）
- [x] `calculate_tier_score` 综合分权重计算正确（单元测试）

### 8.3 投稿判定层
- [x] 硬门槛不足时 `can_submit_to` 返回 `False` 和原因（单元测试）
- [x] 每种判定结果（直接接受/小修/降档/大修/拒稿/Desk Reject）均有覆盖（单元测试）
- [x] 降档规则正确执行（单元测试 `test_top_downgrades_to_disciplinary` 等）

### 8.4 状态流层
- [x] `research.phase` action "5" 进入 `research.submission_target`
- [x] `research.submission_target` 展示当前论文评分（四维分数 + 五层期刊门槛）
- [x] `research.submission_target` 选择目标后调用 `journal_system.review_paper()`，结果文本通过 `StateResult(result, pop_state=True)` 返回，再回到 `research.phase`

> 注：实际实现未引入独立的 `research.review_result` 状态，判定结果作为消息文本随 `pop_state` 直接呈现。GDD 原方案中第 4 项已被简化方案替代。

### 8.5 异常事件层
- [x] `get_anomaly_chance` 返回概率在 `[0, 0.45]` 范围内（单元测试 `test_capped_at_max`）
- [ ] 触发异常事件后通过 `EventFlowController` 正确推入 `input.event_choice`（**仍待实现**：当前 `roll_anomaly_event` 选出事件 dict，但 `review_paper` 仅将其挂在 `result["anomaly_event"]`，未推入 flow）
- [ ] 事件效果正确应用到玩家属性（**仍待实现**：`sanity_min/max`、`mutation_min/max`、`truth_gain` 还没有写回 `Player`）

### 8.6 端到端
- [x] Console 模式可完成：撰写论文 -> 投稿 -> 选择期刊 -> 查看结果 -> 返回科研状态
- [x] `python -m unittest discover` 全部通过（截至 2026-05-01，45 项测试全绿）
