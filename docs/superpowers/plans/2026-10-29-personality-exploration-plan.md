# 心理探索 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. 本文件按实际交付更新完成状态，不宣称未执行的提交或验证。

**Goal:** 从当前对话提取可核对的 MBTI 风格偏好线索，并提供六份独立的本地问卷和用户自我确认。

**Architecture:** `personality.py` 负责有限预算的用户文本推测和原话校验，`personality_questions.py` 负责八题原创偏好自述；`psychometrics.py` 统一完整作答和正反向计分。`ExplorationState` 位于 `exploration_state.py`，作为每个 `Conversation` 的独立状态；`exploration_ui.py`、`personality_ui.py`、`questionnaire_ui.py` 提供入口、同意门槛和本地问卷，支持性聊天管道保持独立。

**Tech Stack:** 现有 Python/Pydantic/Streamlit/pytest，不增加依赖。

**Spec:** [2026-10-29-personality-exploration-design.md](../specs/2026-10-29-personality-exploration-design.md)。

## Global Constraints

- 仅限成年人虚构案例的本地非商业研究，不输出诊断、人格准确率、常模百分位或验证过的稳定类型。
- 自报 MBTI 标签及片段不能作为行为证据；用户原话和助手文字严格区分；未知和矛盾保留。
- 六份问卷与八题偏好自述本地处理，不自动发送模型；对话分析需单独同意并主动点击，每次最多 2 次请求，共享 40 秒截止时间。
- 依恋 12 题与应对信心 6 题为原创未经验证练习；四份既有量表的中文研究自译未经中文信效度验证；SWLS 仅限非商业研究。
- 数据按对话在会话内存中隔离，探索单独导出，报告不包含 API 配置或内部指纹。

## Review Focus

- 引用不存在、属于助手、仅为类型代码或片段时，不能建立四维支持；提示词与字面校验不被描述为语义准确性保证。
- 反向题、缺题和非法取值严格处理；TIPI 情绪稳定性与 Mini-IPIP 负性情绪倾向保持各自方向。
- 切换关系后新答案不混入旧关系结果；旧结果仍携带原关系标签。
- 新对话隔离，清空或移除后状态及控件不复现旧答案；失败和过期观察明确提示。
- 浏览器草稿跨探索切换和计分保留；本地问卷不产生隐藏 API 调用，导出保持主动操作。

## 已交付任务

- [x] Task 1 对话推测：`personality.py`、`prompts/personality.md` 和 `tests/test_personality.py`；四维唯一性、字面原话、助手隔离、未知/矛盾、离线不伪造结果、预算和安全错误码已覆盖；独立审查发现的类型标签片段绕过已修复并加入回归。
- [x] Task 2 偏好自述：`personality_questions.py` 与对应测试实现八题原创问答，同向、矛盾、未知、非法选项和自我确认分别处理，不调用 API。
- [x] Task 3 统一计分和题库：`psychometrics.py`、`attachment_questions.py`、`published_personality_tests.py`、`wellbeing_tests.py`、`research_wellbeing_tests.py`、`exploration_catalog.py`；六问卷实际为依恋原创 12、Mini-IPIP 20、TIPI 10、RSES 10、应对原创 6、SWLS 5 题，保留来源/许可/自译限制及完整正反向计分。
- [x] Task 4 会话状态：`exploration_state.py` 的 `ExplorationState` 集成 `Conversation`；隔离、清除、控件清理、过期提示、失败保留、关系标签和不含内部配置的报告已实现。
- [x] Task 5 页面：顶栏心理探索与七工具目录，单独分析同意和主动按钮、四维依据、原创自述、自我确认、本地问卷、缺题提示、关系切换及分别下载；AppTest 和实际浏览器覆盖相关路径。
- [x] Task 6 验证与说明：完整回归 226 passed in 13.31s；独立审查完成；两段明确虚构成年日常偏好的 DeepSeek 分析一次请求返回正常且字面引用全部校验；实际浏览器验证目录、SWLS 中项 20/35、导出按钮可见及草稿跨切换保留；已有目录和窄屏 SWLS 截图；README、工具说明和执行记录更新。

验证命令：`python -m pytest -q`。具体本轮记录及截图见 [v03-verification.md](../../v03-verification.md)。本目录无 Git 仓库，未声称提交或工作树交付。实际 API 仅验证接通、结构和原话链路，不构成人格准确性或实际账单验证；浏览器导出按钮可见不等同于已核对下载文件内容。

## 本轮范围外

- [ ] 原创练习及中文译文的信效度研究、独立人格准确性评估。
- [ ] 专业审核、真实用户试用审批和相关数据流程。
- [ ] SWLS 商业使用授权；当前仅非商业研究，不以本轮交付推定已获得。
