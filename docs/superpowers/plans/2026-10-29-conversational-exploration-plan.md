# 多版本问卷与对话探索 Implementation Plan（建议稿）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. 2026-10-29用户批准实施后，Tasks 1–5工程功能已交付并通过296项测试；本计划保留原步骤供追溯，实际结果见docs/v04-progress.md。Task 6中的独立人工标注/真实人群验证仍待完成，不能以模型合成测试代替。

**Goal:** 增加真实版本身份的多题数问卷目录，并在明确授权后按对话量积累、检查和展示带依据的性格与关系观察。

**Architecture:** 保留当前支持性聊天管道；量表目录和计分独立于对话观察。调度器在正常聊天完成后提交不可变快照，本机任务返回后由主线程核对授权/会话代际并展示结果。

**Tech Stack:** 现有Python、Streamlit、Pydantic、pytest和DeepSeek；第一版无新增外部数据库/训练平台依赖。

**Spec:** [设计建议稿](../specs/2026-10-29-conversational-exploration-design.md)。默认值为本次建议，不标成已经批准的测量阈值。

## Global Constraints

- 当前仍限成年人虚构案例、非商业研究；真实用户研究不由本任务自动启用。
- 不把聊天变成问卷分数，不把大五变换为MBTI，不混合不同关系。
- 自动分析默认关闭；首次20条候选用户消息且至少1,000非空白字符，之后新增10条；每会话最多3次自动整理，每次最多2请求/40秒。
- 手动、自动和结构修复共享每会话6次额外请求额度；原子预留，已发送失败/超时不返还。
- 每个方向初步要求3条用户消息/3个不同事件/2类情境，反例与未知保留；这是工程门槛而非有效性保证。
- 主聊天、问卷和观察结果分别处理；任何后台失败不得阻断已经生成的聊天回复。
- 不默认持久化，不复用用户数据训练，不默默压缩现有支持流程的安全信息。

## Review Focus

- 同一事件拆成多条、重复粘贴、长但无关文字，不应被视为充分心理证据。
- 他人话语、角色扮演、当前状态、否定和纠正，不应变成本人稳定偏好。
- 伙伴/朋友/不同家人切换不串用，未知关系不硬归类。
- 刷新/清除/撤回授权/旧任务迟到不覆盖当前会话或恢复已删除观察。
- 不同量表/版本/中文材料分数不混比；没有新内容的页面重跑不能重复计费。

## Task 1：问卷版本目录与首批版本

**Files:** 新建 `support_agent/survey_registry.py`；修改 `exploration_catalog.py`、`questionnaire_ui.py`；新增 `tests/test_survey_registry.py`。

**Interfaces:** `SurveyVersion`持有构念、工具、版本、语言、题数、计分键版本、许可与验证人群；`list_versions(construct_id)`返回可见版本；`get_version(version_id)`返回唯一版本定义，不按题数猜测身份。答案/结果/控件/导出使用完整版本身份，必要扩展现有`QuestionnaireResult`，不复用旧题号作唯一键。

- [ ] 先写测试：TIPI10/Mini-IPIP20/IPIP50不同ID；SWLS3/5不同总分范围；禁用未核实中文/许可的版本；未知ID拒绝；情绪稳定/负性情绪方向说明存在；切换两个共享题号的语言/计分版本，答案与控件不串用，结果和导出可追溯。
- [ ] 运行 `python -m pytest tests/test_survey_registry.py -q` 确认因缺接口失败。
- [ ] 实现目录，保留既有定义兼容；第一批接IPIP50，SWLS3在中文题文/授权记录核实后启用；IPIP100、BFI-2和ECR各版按独立来源核实后逐个接入。
- [ ] 用作者计分键核对题文/正反向/端点，运行目录及既有psychometrics测试。

## Task 2：带来源的对话观察

**Files:** 新建 `support_agent/conversation_observation.py`、`tests/test_conversation_observation.py`；完善独立候选 `prompts/conversation_observation.md`。不替换临床信息整理提示词。

**Interfaces:** `ObservationSnapshot`为用户消息、会话代际、授权主题、观察修订与纠正约束的不可变输入；`Observation`包含domain/dimension/direction/subject/scope/relation_context/relation_id/event_id/evidence/counter_evidence；证据逐项关联事件、情境与匿名关系对象。`analyze_observations(snapshot,gateway,budget)->ObservationReport`返回通过校验的观察或安全错误码。提示词/schema只请求授权主题，本机拒收越界主题。

- [ ] 先写字面引用、助手来源拒绝、错误ID、空证据、资料内指令、否定/纠正、重复事件、两位朋友不能共用门槛、对象不明不强归类、只同意MBTI不请求/返回依恋主题的测试；语义边界另由人工标注模型评测覆盖，不把mock通过当语义正确。
- [ ] 确认失败后实现严格schema、连续原文与来源校验、未知/矛盾保留；沿用可控预算与安全错误码，不打印provider异常体。
- [ ] 不自动填充问卷选项；需要的原话因上下文限制不可用时不保留无依据的方向。
- [ ] 测试20条以前先触及字符边界：明确提示可主动查看/导出/另开会话，不偷删聊天，不发送超限快照；报告写明实际范围。
- [ ] 运行新测试与现有personality测试；检查合成语义反例报告。

## Task 3：授权、门槛与调用去重

**Files:** 新建 `support_agent/observation_scheduler.py`、`tests/test_observation_scheduler.py`；扩展 `exploration_state.py`。

**Interfaces:** `ObservationSettings`含enabled/domains/revision；`should_schedule(state,snapshot,decision)->ScheduleDecision`纯函数；`mark_scheduled(snapshot_id)`确保同一快照只启动一次；手动与自动共用原子请求预留器，修复请求同样消耗额度。

- [ ] 测试未授权20条不启动、19条不自动启动、字符不足不启动、助手/空白不计数、同快照rerun不重复、未新增10条不重跑、三次上限、手动不绕过6请求额度、并发预留不超限、失败/超时已发请求不退回、暂停和紧急支持优先。
- [ ] 确认失败后实现确定性计数、阈值、快照哈希、预算和手动入口；明显重复只计一次，内容质量仍交由后续证据检查。
- [ ] 运行调度器测试；明确记录20/10/3是产品参数而非科学结论。

## Task 4：本机任务与安全回收

**Files:** 新建 `support_agent/observation_jobs.py`、`tests/test_observation_jobs.py`；修改 `ui.py`、`conversations.py` 的必要接点。

**Interfaces:** `submit(snapshot,settings)->job_id`每会话最多一个；`poll(job_id)->JobResult|None`非阻塞；`accept_result(result,conversation,settings)->bool`核对会话ID/代际/授权版本/观察修订号。线程不访问Streamlit状态。

- [ ] 测试慢任务不阻断回复、清空后旧结果被丢弃、整段删除/单条删除/撤回/标为状态/不认同后旧任务不恢复记录、后续快照继续遵守纠正约束、切换会话隔离、失败保留旧报告、过期结果标明快照、超时不无限重试。
- [ ] 确认失败后实现线程与锁边界，主线程以Streamlit片段轮询，不设置无限后台任务。
- [ ] 运行新测试与现有conversations/AppTest；检查总调用量及错误恢复。

## Task 5：可修正的探索页面

**Files:** 修改 `exploration_ui.py`、`questionnaire_ui.py`、`assets/chat.css`；新建 `observation_ui.py`、`tests/test_observation_ui.py`。

- [ ] 测试默认关闭、主题选择、授权信息、信息不足/反例/关系分组、查看原话、标为当前状态/不认同/删除、撤回分析、单独导出、未授权无隐藏请求。
- [ ] 实现“轻提示→自行展开报告”，不以强制弹窗打断聊天；用已确认沟通偏好调整呈现，推测人格不改变支持或安全策略。
- [ ] AppTest通过后检查实际浏览器：授权→20条合成消息→报告/不足→补问可跳过→切关系→撤回→迟到结果丢弃；检查窄屏与草稿保留并保存截图。

## Task 6：提示词评测与发布验收

**Files:** 使用 `scripts/eval_conversation_observation.py` 与合成案例；另增冻结的开发/验证/测试数据，结果写 `reports/`，更新工具说明。

- [ ] 首轮3次请求合成试测只报告观察结果，不宣称准确率提升。
- [ ] 扩展100个独立人工标注的合成案例，按人物/事件/模板分组60/20/20；冻结测试集不参与提示词迭代。新增真实API批次先确定请求/token预算。
- [ ] 比较当前方案与候选提示词的相同保留集，报告误归因/关系串用/强判/反例丢失/结构/成本；关键已知反例出现错误先修复，不扩大调用量掩盖失败。
- [ ] 运行 `python -m pytest -q`；以真实输出和退出码记录结果，不沿用先前226测试的旧计数作为新增功能通过证据。
- [ ] 量表题文、许可、版本与中文状态人工核对；完整浏览器验收后再启用新功能。此目录无Git仓库，不虚构提交；若将来纳入版本控制再按实际流程记录。

交付分两段：先完成版本目录/首批问卷与手动对话观察，再接自动调度和任务管理。真实用户测量有效性、跨会话记忆及权重微调是独立后续项目，不以完成上述软件任务推定通过。
