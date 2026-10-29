# 对话观察候选提示词首次试测

日期：2026-10-29。用户已允许使用现有DeepSeek API，并选择“优化提示词和效果”。本轮只做独立候选提示词与合成案例试测，没有改变模型权重，没有把自动分析或新量表版本接入应用。

## 已完成

- 候选提示词：[conversation_observation.md](../prompts/conversation_observation.md)，覆盖MBTI风格、大五宽维与依恋两维，强调本人经历、状态/习惯、关系情境、引用和反例。
- 三组合成资料：[conversation_observation_seed.jsonl](../data/evaluation/conversation_observation_seed.jsonl)。预期与来源标注只用于本机评测，不发送给模型；不含真实用户材料。
- 可重复评测：[eval_conversation_observation.py](../scripts/eval_conversation_observation.py)。每组最多1请求，无自动修复或重试，总计最多3次。
- 冻结live结果：[conversation_observation_smoke.json](../reports/conversation_observation_smoke.json)。实际3次请求，输入4,708 tokens、输出563 tokens；没有根据价格猜测账单金额。
- 本机自检：[conversation_observation_dry_run.json](../reports/conversation_observation_dry_run.json)。三份参考输出与八类错误变体的接受/拒绝检查通过；根代理重跑dry-run后，live报告内容哈希保持不变。自检是验证有限检查器，不代表能识别任意语义错误。

## 本次结果

| 案例 | 冻结结果 | 解释 |
| --- | --- | --- |
| 本人独处习惯＋伴侣关系焦虑 | checks_failed | 返回EI=I与伴侣焦虑，原话等检查通过，但未输出预设要求的大五外向性条目 |
| 朋友经历＋角色扮演＋一晚睡差 | passed | 没有把这些内容变成用户本人的长期特质，返回空观察 |
| 伴侣反例＋朋友的不同模式 | passed | 伴侣焦虑保留mixed与反例，朋友关系单独记录 |

总结果保留为failed，未在看过输出后修改预期或重跑直到成功。2/3是有限预设检查的结果，不能写作人格准确率66.7%。案例一的“大五条目必须出现”是一项需要人工复核的框架覆盖预期：EI偏向独处不自动等于完整的大五外向性偏低；谨慎省略不必然是错误。后续应分别衡量覆盖率和错误强判，而不是迫使模型为了过测补齐维度。

候选v1使用两条消息的基础证据协议；制作方案提出的20条调度、3事件/2情境门槛、匿名关系对象、主题授权与后台任务均尚未实现。不能把本次试测当作自动功能上线验证。

## 下一轮如何优化

1. 先人工审查哪些是必需的观测、哪些允许未知或省略，独立标注支持方向与相反证据；不由同一模型给自己判对。
2. 将不同框架分别评估，避免MBTI与大五之间的隐式换算。扩充转述、否定、角色扮演、重复拆消息和同类关系不同对象案例。
3. 冻结开发/验证/测试划分，并记录请求模型别名、可获得的模型版本、提示词/数据哈希、运行时间、错误及用量。本次报告已记录提示词与数据哈希，未记录可复现的后端模型版本，不能用于细致的跨版本归因。
4. 使用同一保留集做基线与候选对照，分别报告误归因、反例丢失、关系串用、覆盖、强判和成本。首轮没有基线对照，不能宣称优化提升已经被证明。

无网络自检命令：

```powershell
.\.venv\Scripts\python.exe scripts\eval_conversation_observation.py --dry-run
```

`--live`会再次产生最多3次付费请求；本轮没有追加运行。当前脚本的live路径会写入该次结果，复测前应将上一轮报告另行归档。产品方案与后续任务见[设计建议稿](superpowers/specs/2026-10-29-conversational-exploration-design.md)和[制作计划](superpowers/plans/2026-10-29-conversational-exploration-plan.md)。
