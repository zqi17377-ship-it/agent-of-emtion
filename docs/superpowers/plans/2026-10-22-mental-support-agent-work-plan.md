# 中文心理支持 Agent 详细工作计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 8 周内完成一个基于中文成年人虚构案例、可以本地演示和回归测试的心理支持研究原型，为后续专业审核和受监督试用准备材料。

**Architecture:** 使用现成模型理解用户自述，由 Python 校验状态并选择回应动作，检索审核过的知识卡后生成回复，再进行输出检查。安全相关流程优先于普通支持流程，所有外部请求具有次数和时间限制。

**Tech Stack:** Python 3.12、Pydantic 2、Streamlit、pytest、一个可替换的模型 API 适配器；本地 Markdown/JSON/JSONL 文件存储研究资料。

**Spec:** [计划设计基线](../specs/2026-10-22-mental-support-agent-design.md)。执行者先读设计基线，再按本计划推进。

**计划日期：**初稿 2026-10-22，完成修订 2026-10-23。周次相对实际开工日计算，尚未替用户预约时间或开通付费服务。

**执行记录（2026-10-29）：**已实施离线工程框架；真实模型与专业审核待完成。详见[实施状态](../../implementation-status.md)与[验证和决策记录](../../execution-progress.md)，未完成的外部验收不因代码交付而自动勾选。

## 一、怎么使用这份计划

你只需要先看第 1～5 部分，再按每周任务执行。接口、文件名和测试命令是给后续实现者的工作说明，不要求开始前全部掌握。

本计划按每周 10 小时核心工作 + 最多 2 小时缓冲估算，8 周共 80～96 小时，前提是有 AI 编程或熟练实现者协助、模型接口及时可用，资料和案例可先生成草稿再审核。若你主要独立边学边写，建议把同一组任务安排为 12～16 周、约 120～192 小时。两者都是估算，专业人员工作、资料授权和外部等待另计。超过一周的延期应缩小功能或延后时间，不省略必要验证。

80～96 小时表示你本人参与学习、资料整理、运行检查和验收的计划投入，并非全团队总工时；另请开发者或专业人员时，其投入和费用单独记账。AI 辅助生成的内容仍需你或相应专业人员检查。

第 2 周结束后用实际速度重新估算：统计整理一张知识卡、编写和检查一个案例各需多久，再乘剩余数量。40 张知识卡和 120 个案例包含持续的编写与检查工作，不能把模型批量生成文件当作已经审核完成。

你已经确认的是“个人研究、最终面向用户、会一点 Python”。中文成年人、文字场景和上述时间安排是本计划的默认假设。没有确认服务商或预算也能先用虚构数据和模拟接口推进。

## 二、最终要拿到什么

| 交付物 | 具体内容 | 完成证据 |
|---|---|---|
| 本地研究原型 | 一个可输入和回复中文的聊天页面；后台展示结构化状态和动作 | 能按 README 启动，用演示案例完成多轮对话 |
| 知识资料包 | 40 张有出处、适用范围和授权记录的知识卡 | 授权、内容审核状态可筛选；不合格内容不进入可发布包 |
| 场景与测试包 | 80 个开发场景 + 40 个保留场景，按家族隔离 | 有清单、版本和分组检查结果 |
| 规则与安全流程 | 五种回应动作、失败处理、实际求助能力说明 | 已定义规则全部通过确定性测试 |
| 评测报告 | 逐例结果、主要错误、使用成本、延迟、专业审核状态 | 结论区分技术运行、用户体验和临床能力 |
| 下一阶段清单 | 专业审核、受监督试用和上线准备的条件 | 每项标记负责人、证据和是否满足 |

第 8 周应交付“可演示、可回归测试、专业审核状态明确的研究原型”。不能把“所有演示通过”改写成“能够诊断”或“已经适合公开使用”。

交付状态分开记录：A“离线工程框架”只要求模拟接口和确定性测试通过；B“模型接入版研究原型 v0.1”还要求真实模型评测、运行记录和已知缺陷处理完成；C“可开始受监督试用”必须满足第十二部分的全部准入条件。没有 API 时可以完成 A，不能把模拟响应当作 B 的模型能力证据。

## 三、Global Constraints

以下项目与设计基线保持一致，适用于所有任务：

- 运行环境：Windows，本地开发；目标 Python 3.12，依赖在首次兼容性验证后锁定具体版本。
- 技术栈：Python、Pydantic 2、Streamlit、pytest，以及最终选定服务商的接口适配器；首版不依赖复杂 Agent 框架或向量数据库。
- 面向对象：中文成年人；首版真实数据留存默认关闭。
- 对话数据：原型只保存在当前会话内存中；清除会话后不得继续用于上下文；供应商侧留存须另行核查，不能承诺随本地清除而删除。
- 日志：不记录用户原文、模型完整回复、API 密钥或用户身份；测试报告只允许包含虚构案例。
- 数据使用：授权状态不明确的内容不得进入可分发的知识库、训练材料或产品；用户对话不得默认进入训练集。
- 判断：允许未知、矛盾、多种困扰并存；没有识别到线索不等于排除风险。
- 回应动作：listen、clarify、support、refer、urgent_support。
- 量表：PHQ-9/GAD-7 等不是首版必需功能；后续使用需核对版本、授权、适用人群，并由程序按正式规则计分。
- 安全：不用量表分数或低中高分层预测未来自杀、自伤；不把模型自报置信度当作医学概率。
- 检索：先使用知识卡的人工标签和关键词；每次最多返回 3 张，空结果保留为空；未授权、未审核或不适用于当前人群的卡片不可用于真实用户回复。
- 调用控制：每轮最多 4 次外部模型请求，失败请求计入；单次超时 20 秒、整轮截止 45 秒；生成内容在检查前不向用户流式输出。
- 故障：模型、校验或知识库故障有明确状态与备用回复；不能把失败解释为用户安全。
- 上下文：超出模型上下文或预算时明确返回受限状态，不静默删除尚未澄清的安全线索；所有证据保持消息引用。
- 原型与真实用户试用之间设置独立验收；8 周结束不自动启动真实用户试用。

研究期间可使用明确标为未审核的自编卡片进行虚构案例测试；这不等于允许其进入真实用户服务。资料筛选直接使用 SessionState.mode：synthetic_research 允许使用授权明确、内容未审核的虚构研究资料；eligible_pilot 额外要求内容和适用性审核完成。后者只实现过滤规则并测试，真实用户试用条件满足前不提供启用入口。

## 四、8 周里程碑与依赖

| 周次 | 核心工作，约 10 小时 | 本周交付物 | 进入下一步的条件 |
|---|---|---|---|
| 第 1 周 | 确定范围 2h；环境与基本调用 4h；模拟接口和错误处理 4h | 可运行的命令行对话、环境记录、服务商比较表 | 模拟模式可运行；真实 API 条件未就绪时后续继续用模拟数据 |
| 第 2 周 | 来源与授权 3h；知识卡 3h；标注规则与首批案例 4h | 来源清单、20 张知识卡、20 个开发案例 | 每条数据都有来源和使用状态，能区分知识/示例/测试 |
| 第 3 周 | 状态字段与校验 3h；提取实现 4h；证据和异常测试 3h | 结构化评估模块、累计 40 个开发案例 | 不虚构证据；缺失字段保留未知；失败有明确状态 |
| 第 4 周 | 回应策略 3h；安全流程和备用回复 4h；多轮规则测试 3h | 五类动作、场景处理表、累计 60 个开发案例 | 即时安全支持优先，未知不默认安全，没有虚假转介 |
| 第 5 周 | 资料扩充与检索 3h；回答生成 4h；输出检查 3h | 40 张知识卡、完整对话流程、80 个开发案例 | 空检索、未授权内容和模型异常均有明确行为 |
| 第 6 周 | 本地页面 4h；会话隔离与清除 3h；日志和调用统计 3h | 可演示页面、隐私说明、数据流图 | 两个会话互不泄露，清除生效，日志不含敏感原文 |
| 第 7 周 | 建立并冻结 40 个保留案例 2h；评测与评审 4h；缺陷归类 4h | 首轮评测报告、专业意见或缺失说明、问题清单 | 明确漏检、误报和严重问题，保留集未被用于调参 |
| 第 8 周 | 修复与回归 5h；成本/延迟和使用说明 2h；演示与下一阶段评审 3h | 研究原型 v0.1、复现说明、试用条件清单 | 技术验收通过，限制与未完成专业审核如实记录 |

依赖主线：1 → 2 → 3 → 4 → 5 → 6 → 7 → 8。知识资料审核和联系专业人员可从第 2 周开始并行。不要等到第 8 周才寻找审核资源。

## 五、第一周每天具体做什么

| 工作块 | 约 2 小时内的动作 | 当天可检查的结果 |
|---|---|---|
| 第 1 天 | 写明目标人群、压力/情绪低落/睡眠/人际四类困扰、用途边界；检查 Python；整理两家候选模型服务商 | 一页范围说明和服务商比较表，暂不提交真实对话 |
| 第 2 天 | 建虚拟环境；学习字典、函数、JSON 和异常处理；建立忽略文件和依赖记录 | 能读取虚构消息 JSON，密钥文件不会加入版本管理 |
| 第 3 天 | 实现模拟模型；如服务商就绪，接通一次真实请求 | 终端能发送一句虚构消息并获得回复 |
| 第 4 天 | 实现多轮上下文和 /clear；加入超时、认证失败、限额错误处理 | 能完成三轮聊天，清除后不再带入前文 |
| 第 5 天 | 跑接口测试；记录用量；写启动说明和本周遇到的问题 | 他人可按说明运行模拟模式；API 模式状态明确 |

学习只围绕当周需要：第 1 周理解 JSON/API，第 3 周学习数据校验，第 4 周学习条件分支，第 6 周学习简单页面。不安排完整机器学习课程作为前置条件。

## 六、数据获取与加工计划

### 6.1 数据来源及用途

| 来源 | 获取动作 | 允许承担的角色 | 要核查的条件 |
|---|---|---|---|
| [WHO mhGAP](https://www.who.int/publications/i/item/9789240084278)、适用的专业指南 | 阅读与定位相关章节，记录版本；编写有依据的知识卡 | 参考知识和专业审核依据 | 下载可读不等于可商用转载；内容使用、改编、翻译分别核查 |
| [PsyQA](https://github.com/thu-coai/PsyQA) | 查看样例；需要全量时按项目要求签协议申请 | 许可范围内研究中文支持策略 | 不推定商业授权；论坛问题和主题不是确诊标签 |
| [ESConv](https://github.com/thu-coai/Emotional-Support-Conversation) | 阅读官方说明和许可证后决定是否用于研究 | 理解倾听、澄清、情绪回应等策略 | 项目有非商业、学术研究限制；翻译不改变原许可 |
| [DAIC-WOZ](https://dcapswoz.ict.usc.edu/) | 首版仅了解，不列为必需下载项 | 后续特定筛查研究 | 受非营利研究及申请条件限制；PHQ-8 标签不是医生确诊 |
| 自编虚构场景与专业审核示例 | 自己编写或用模型辅助生成，再逐条审核 | 开发、模拟演示、独立评测 | 明确为合成数据；不据此宣称真实用户效果 |
| 真实用户或医疗机构数据 | 在后续阶段单独设计获取流程 | 合法授权范围内的研究或产品改进 | 目的、同意、伦理、去标识、保存期限、服务商处理条款均需落实 |

任何时候都不要从私人咨询记录、聊天群或泄露资料中直接收集训练数据。公开帖子也不能因为可浏览就被视为已获产品使用授权。

### 6.2 三类资料分开保存

1. 知识卡：用于回答时检索，不是用户病历。
2. 开发案例与示范：用于设计提示词、规则和回归测试。
3. 保留案例：用于最后检验，不能直接复制到提示词或知识库。

每张知识卡记录：id、主题、正文、适用条件、不适用条件、来源 URL、文献日期、审核日期、使用授权凭据、审核人、审核状态。翻译或改编时同时记录原文出处与衍生使用许可。

每个案例记录：id、scenario_family、语言/目标人群、完整对话、预期可接受动作、必需行为、禁止行为、风险线索证据、是否合成、编写者、审核者、split。动作允许多个合理选项，不强求每个正常对话只有一个固定答案。

### 6.3 初始数量与覆盖

40 张知识卡可先按压力 12、睡眠 10、情绪低落 10、人际困扰 8 分配。安全回应与专业转介策略单独维护，不作为普通安慰资料混入检索。数量不是医学充分性标准。

120 个案例按主标签分配如下，允许附加标签：

| 主标签 | 数量 | 例子或覆盖要求 |
|---|---:|---|
| 日常支持 | 30 | 工作压力、关系困扰、短期情绪变化、只想倾诉 |
| 持续困扰和生活影响 | 20 | 长期睡眠问题、工作学习受影响、持续低落 |
| 信息不足或矛盾 | 20 | 时间不明、说法变化、转述别人、明确拒绝量表 |
| 安全支持情境 | 20 | 明确/隐晦表达、多轮后期升级、否认后补充信息 |
| 其他专业评估线索 | 10 | 异常兴奋少睡、冲动、幻听体验、用药相关求助 |
| 提示注入与隐私 | 10 | 要求忽略规则、索要其他会话、诱导暴露密钥 |
| 服务异常 | 10 | 超时、限流、无效 JSON、空检索、检查器失败 |
| 合计 | 120 | 按家族分组划为开发 80 / 保留 40，两个集合都覆盖各大类 |

真实人员或同一合成场景的所有轮次、近似改写都归在同一组。由另一名编写者或专业审核者准备保留集更好；只能自己准备时，要在报告中说明独立性限制。

数据处理顺序：确认来源与权限 → 去除不必要个人信息 → 去重与家族分组 → 标注 → 专业审核或明确未审核 → 分开发/保留 → 冻结版本。去掉姓名不等于完全匿名。

## 七、项目文件与模块分工

以下是计划创建的文件，不代表现在已存在：

```text
app.py                          本地 Streamlit 页面
requirements.in                 直接依赖范围
requirements.txt                实测后锁定的完整依赖
.env.example                    配置字段示例，不含真实密钥
.gitignore                      排除密钥、环境和个人数据
README.md                       启动、演示、限制与故障说明
support_agent/
  __init__.py
  config.py                     读取配置、超时与调用限制
  schemas.py                    模块之间传递的数据结构
  model_client.py               真实接口与模拟接口
  cli.py                        命令行入口
  assessment.py                 状态提取与原文证据校验
  policy.py                     回应动作选择
  knowledge.py                  卡片读取、过滤与检索
  response.py                   回复生成
  guardrails.py                 输出检查
  workflow.py                   整轮流程、截止时间和备用回复
  session.py                    会话创建、清除与隔离
  telemetry.py                  不含原文的用量、耗时和错误统计
prompts/
  assess.md                     结构化提取提示词
  respond.md                    回复提示词
  check.md                      检查提示词
policies/
  actions.json                  五类动作与优先级
  fallbacks.json                固定备用回应
  help_resources.json           经核实的地区求助资源，不编造号码
data/
  sources.json                  来源、授权和审核记录
  knowledge/cards.jsonl         知识卡
  eval/dev.jsonl                开发案例
  eval/holdout.jsonl            冻结后的保留案例
scripts/
  __init__.py
  check_data.py                 数据格式、分组与授权校验
  evaluate.py                   运行场景并生成报告
tests/                          可离线运行的确定性测试
reports/                        仅保存虚构案例的评测输出
docs/                           范围、数据、流程与试用文件
```

小型知识库先用标签/关键词检索，避免提前引入向量服务和更多数据处理方。是否升级检索由第 7 周的漏检结果决定。

### 统一接口约定

类型由 schemas.py 定义，所有模块复用，禁止各自发明一套字段。

| 类型 | 字段及含义 |
|---|---|
| Message | id、role（user/assistant）、content |
| Evidence | id、message_id、quote；quote 必须能在对应用户消息中定位；id 由程序按消息与引文位置生成，保证引用稳定 |
| SafetySignal | id、kind（self_harm/harm_to_others/other_urgent/needs_professional_assessment）、subject（self/other/quoted/unknown）、timeframe（current/past/unknown）、assertion（reported/denied/unclear）、current_need（immediate_support/clarify/professional_review）、evidence_ids；current_need 是根据明确原文和策略表建议的当前行动，不是未来风险概率，证据不足时取 clarify |
| SignalClarification | signal_id、new_evidence_ids、reason（subject_or_context_corrected/additional_information）；只记录澄清建议，是否改变状态由策略表校验 |
| Assessment | concerns、duration、daily_impact、user_goal、evidence、safety_signals、clarifications、missing_information、status（ok/insufficient/failed）；未知字段为 null 或空列表，不能补造 |
| Action | listen/clarify/support/refer/urgent_support |
| Decision | action、reason_codes、evidence_ids、unresolved_safety: list[SafetySignal]、clarification_log: list[SignalClarification]；保留尚未澄清的线索和状态变化依据，不是已确诊标签 |
| KnowledgeCard | id、title、content、tags、source_url、source_date、permission_status、permission_evidence、review_status、reviewer、review_date、applicability、exclusions；permission_status 取 permitted/research_only/unknown/prohibited，review_status 取 pending/approved/rejected；research_only 的具体用途还须核对 permission_evidence |
| EligibilityContext | adult_status（confirmed/unknown/minor）、language、reported_conditions、use_purpose；成年人状态与条件来自明确的场景资料或用户提供的信息，缺失条件不推断为满足 |
| CheckResult | allowed、reason_codes；格式失败一律不能当作通过 |
| TurnResult | text、action、source_ids、status（ok/fallback/error）；内部调试状态与普通用户界面分开 |
| ModelResult | text、input_tokens、output_tokens、model_id；没有返回用量时记录 unknown，不能计为 0 |
| SessionState | messages、previous_decision、eligibility: EligibilityContext、mode（synthetic_research/eligible_pilot）；后者在试用条件满足前禁用 |
| CallBudget | limit=4、deadline_seconds=45、attempts；所有模型模块共享同一实例，失败请求同样递增 |

SessionState.mode 不是自行宣称符合试用条件的开关；是否启用由真实用户阶段的发布检查决定。原型只启用 synthetic_research。

## 八、逐项实施任务

约定：每项先为重要行为写测试并确认能发现错误，再实现，通过后记录结果。纯文档或简单界面排版用人工检查，不为它们编写形式化测试。若建立 Git 仓库，每项完成后提交一个可回退的版本，提交前确认没有密钥与私人资料。

### Task 1：环境、模型接口与可运行命令行（第 1 周）

**Files:** 创建 requirements.in、requirements.txt、.env.example、.gitignore、README.md、pytest.ini、support_agent/__init__.py、config.py、schemas.py、model_client.py、cli.py、tests/conftest.py、tests/test_model_client.py、docs/provider-choice.md。

**Interfaces:** 定义 Message、ModelResult、CallBudget；ModelGateway.generate(messages: list[Message], instructions: str, schema: dict | None, budget: CallBudget) -> ModelResult；FakeGateway 实现同一接口。instructions 只能来自程序管理的提示词，用户消息和检索资料不能提升为系统指令。接口失败抛 ModelCallError，包含 auth/rate_limit/timeout/invalid_response/context_limit/unavailable 中的原因码，不含响应原文或密钥。

- [ ] 写范围说明；比较两家可用服务商的中文表现、结构化输出、数据使用/保存、地区和实际收费，记录官方来源与核查日期。
- [ ] 使用虚构数据确定一个模型 ID；未有可用 API 时使用 FakeGateway，不让账号申请阻塞整个项目。
- [ ] 建立虚拟环境，安装最少依赖，验证后锁定版本；配置字段为 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL，真实值只保存在本机配置中。
- [ ] 定义上述数据类型和接口；加入 test_timeout_is_explicit、test_failed_calls_consume_budget、test_secret_not_in_error、test_mock_mode_needs_no_key，先确认未实现时失败。
- [ ] 增加 test_only_trusted_instructions_map_to_system，检查服务商请求中用户内容不会被拼成系统指令。
- [ ] 实现接口和命令行入口；请求次数与截止时间由统一 CallBudget 记录，适配器不做隐藏无限重试。
- [ ] 支持 /clear；模拟接口完成三轮聊天，真实接口仅跑少量授权的虚构输入。
- [ ] 本周命令行暂用独立的 list[Message] 保存会话；Task 6 改用统一 SessionState 和 clear_session，避免永久保留两套清除逻辑。
- [ ] 运行 python -m pytest tests/test_model_client.py -q；预期全部通过。运行 python -m support_agent.cli --mock；预期能输入、回复、清除。
- [ ] 更新 README，记录模型/依赖版本与 API 未完成事项，保存一次版本。

**验收：**无 API 密钥也能演示流程；超时与错误不伪装成成功；密钥不进入日志、代码或报告。

### Task 2：来源登记、知识卡和场景规范（第 2 周）

**Files:** 创建 data/sources.json、data/knowledge/cards.jsonl、data/eval/dev.jsonl、data/eval/holdout.jsonl（先为空）、docs/data-guide.md、scripts/__init__.py、scripts/check_data.py、tests/test_data.py；扩展 schemas.py 的 KnowledgeCard 和案例类型。

**Interfaces:** validate_assets(root: Path) -> list[str] 返回错误清单；错误为空表示格式、分组与状态字段合格，不表示专业内容正确。

- [ ] 建立来源与权限表，记录研究与产品两种用途是否各自允许；未知记录为 unknown。
- [ ] 编写 20 张知识卡和 20 个开发案例；标出合成与未审核状态。
- [ ] 联系能参与审核的精神科医生/心理专业人员；记录可提供的工作、费用和时间，未确认时不得填写“已审核”。
- [ ] 写 test_duplicate_family_cannot_cross_split、test_missing_license_is_unknown、test_source_required；确认坏样本被拒绝。
- [ ] 实现数据校验器；禁止 sources、cards、cases 中相互引用不存在的 ID。
- [ ] 运行 python -m scripts.check_data；预期正常资料无格式错误，故意重复/缺来源的样本报明确错误。
- [ ] 保存标注说明和本周数据版本，保留集保持隔离。
- [ ] 记录真实的资料/案例处理时间，修订剩余周工作量；安排另一位编写者从第 2 周起准备保留集，第 7 周只做最终校验和冻结。若没有协作者，提前预留自己的额外编写时间并披露独立性限制。

**验收：**随便抽 5 条数据，能够说清来源、用途和审核状态；无人能把问答主题解释为确诊标签。

### Task 3：结构化状态提取（第 3 周）

**Files:** 创建 support_agent/assessment.py、prompts/assess.md、tests/test_assessment.py；扩展 schemas.py 的 Evidence、SafetySignal、SignalClarification、Assessment，并定义后续共用的 Action、Decision 类型。

**Interfaces:** assess(messages: list[Message], previous: Decision | None, gateway: ModelGateway, budget: CallBudget) -> Assessment；previous 只提供已记录的线索与引用，不能作为无需核查的新事实。

- [ ] 写 test_missing_duration_remains_unknown、test_evidence_must_match_user_message、test_quoted_other_person_not_treated_as_self、test_invalid_json_returns_failed、test_conflicting_information_is_retained、test_denial_is_not_reported_as_positive_assertion。
- [ ] 实现结构化提取；识别持续时间、生活影响、需求、原文证据和安全线索，禁止给出医学概率或确诊字段。
- [ ] 校验 evidence 的消息 ID 和原文；模型添加的信息不可直接写入用户状态。
- [ ] 解析失败可在预算内修复一次；仍失败返回 failed，不补造一个“正常”评估。
- [ ] 增加 20 个开发案例到累计 40 个，重点覆盖信息缺失、矛盾和转述。
- [ ] 运行 python -m pytest tests/test_assessment.py -q；预期全部通过；人工检查 10 个虚构输出是否忠于原文。
- [ ] 保存提示词版本与失败样例，不将长模型推理记录为产品数据。

**验收：**有明确依据才填事实；未知、无效输出和没有识别到线索能被区别记录。

### Task 4：动作选择、安全流程与备用回复（第 4 周）

**Files:** 创建 support_agent/policy.py、policies/actions.json、policies/fallbacks.json、policies/help_resources.json、tests/test_policy.py、docs/response-policy.md；复用 Task 3 定义的 Action、Decision。

**Interfaces:** choose_action(assessment: Assessment, previous: Decision | None) -> Decision。策略表和专业审核状态一起管理。

- [ ] 定义五种动作的适用条件：倾听、澄清、日常支持、专业评估建议、即时安全支持；安全支持可以同时表达共情，不等于结束对话。
- [ ] 为当前危险线索、尚未澄清的线索、普通倾诉分别写规则。普通用户未主动提到安全情况时，不机械地逐轮询问自伤问题。
- [ ] 把优先级落实为可测试的策略表：有证据的即时支持需求或前轮尚未澄清的即时需求优先 urgent_support；评估失败且没有已知即时需求时使用服务受限的 clarify 备用回复；待澄清线索优先于常规建议；其他专业评估线索选择 refer；其余按信息缺口和倾听/建议诉求选择 clarify、listen 或 support。混合场景允许一个主动作加支持性表达，禁止只凭关键词或单个量表分数选择紧急分支。
- [ ] 定义线索生命周期：未澄清线索持续保留；新信息提出澄清时，必须引用原线索 ID 和新增原文。明确纠正主体/引用语境可按策略更新；其他情况只有符合已审核的澄清规则才改变当前动作，并保留记录。转移话题、时间过去、模型漏提或单次否认都不能自动清空线索。澄清某一条线索也不表示用户总体安全。
- [ ] 增加 test_clarification_requires_new_evidence、test_topic_change_does_not_clear_signal、test_context_correction_keeps_audit_record；研究阶段未审核的澄清规则标为未审核，不进入真实用户流程。
- [ ] 写 test_urgent_action_has_priority、test_unknown_is_not_safe、test_new_turn_can_escalate、test_unresolved_signal_not_erased_by_topic_change、test_no_human_team_no_transfer_claim。
- [ ] 验证可用求助资源的地区与更新时间；没有查证就不填电话号码；没有人工服务就如实说明能力。
- [ ] 准备适用于模型失败、知识不足和即时安全支持的简短固定文案；真实用户使用前必须由专业人员审核。
- [ ] 增加 20 个案例到累计 60 个，覆盖隐晦表达、后期升级、否认后补充、疑似异常兴奋/感知体验等。
- [ ] 运行 python -m pytest tests/test_policy.py -q；预期所有规则用例通过，并逐例人工核对表达是否误导。

**验收：**已输入的危险状态能触发正确分支；这只能证明路由正确，不能证明模型能识别所有危险状态。

### Task 5：知识检索、回复生成与输出检查（第 5 周）

**Files:** 创建 support_agent/knowledge.py、response.py、guardrails.py、workflow.py、prompts/respond.md、prompts/check.md、tests/test_knowledge.py、tests/test_workflow.py；补齐 schemas.py 的 CheckResult、TurnResult、EligibilityContext、SessionState。

**Interfaces:** retrieve(query: str, concerns: list[str], cards: list[KnowledgeCard], eligibility: EligibilityContext, mode: Literal["synthetic_research", "eligible_pilot"], limit: int = 3) -> list[KnowledgeCard]；draft_reply(messages: list[Message], assessment: Assessment, decision: Decision, cards: list[KnowledgeCard], gateway: ModelGateway, budget: CallBudget) -> str；check_reply(text: str, messages: list[Message], assessment: Assessment, decision: Decision, cards: list[KnowledgeCard], gateway: ModelGateway, budget: CallBudget) -> CheckResult；run_turn(session: SessionState, text: str, gateway: ModelGateway) -> TurnResult。检查器必须能看到相关用户消息和评估依据，才有条件检查是否误读用户或附和异常信念。

- [ ] 把知识卡补足 40 张、开发案例补足 80 个；完成授权检查和内容审核记录。
- [ ] 写 test_unapproved_card_excluded_from_eligible_mode、test_empty_retrieval_does_not_invent_sources、test_urgent_path_skips_normal_retrieval、test_checker_failure_uses_fallback、test_budget_includes_all_stages、test_retrieved_instruction_cannot_override_policy、test_context_limit_does_not_silently_drop_safety_state。
- [ ] 实现标签/关键词检索，记录选中卡片 ID；无匹配返回空，不填充无关资料。
- [ ] 在关键词排序前校验 EligibilityContext：缺少卡片要求的必要条件时排除该卡；出现排除条件时排除该卡。增加 test_unknown_applicability_excludes_restricted_card、test_exclusion_overrides_keyword_match；仅有相似关键词不代表资料适用于用户。
- [ ] 实现回复生成：按用户需求和动作回应，常规情况下只追问 1～2 个关键问题，避免机械长问卷；来源不支持的医学解释不可作为事实输出。
- [ ] 实现规则检查与模型检查，检查确诊/处方/保证疗效/虚假转介/强化异常信念等问题。模型检查失败或无预算时使用固定备用回复，不放行未检查草稿。
- [ ] 备用回复与策略同版本保存，运行时不由模型自由改写；即时安全支持的备用内容不能被普通“稍后再试”覆盖。首次使用前完成对应审核，接口不可用时也能读取本地文案。
- [ ] 整合各步骤，共享每轮调用预算；正常 3 次调用（评估、生成、检查），第 4 次只用于一次必要的格式修复；没有剩余预算时不再自动重试。
- [ ] 运行 python -m pytest tests/test_knowledge.py tests/test_workflow.py -q；预期全部通过。运行开发案例，记录知识缺口、漏检和过度转介。

**验收：**从输入到输出的流程可解释；安全路径、无知识、错误输出与接口失败都有可检查结果。

### Task 6：本地页面、会话隐私和用量统计（第 6 周）

**Files:** 创建 app.py、support_agent/session.py、telemetry.py、tests/test_session_privacy.py、docs/data-flow.md、docs/privacy-prototype.md。

**Interfaces:** new_session() -> SessionState；clear_session(session: SessionState) -> None；record_event(event_type: str, metrics: dict) -> None。metrics 使用字段白名单，只允许模型 ID、用量、耗时、动作、状态、错误原因和匿名运行 ID。

- [ ] 实现本地页面、输入、完整回复展示、清除会话、研究模式提示和开发者调试面板；评估字段不包装为给用户的诊断报告。
- [ ] 写 test_sessions_do_not_share_history、test_clear_removes_history_and_decision、test_logs_exclude_text_and_keys、test_metrics_reject_unlisted_fields。
- [ ] 将会话存入每个会话独立的内存状态，禁止把对话放进共享全局缓存；清除同时清理消息、评估和未解决线索状态。
- [ ] 绘制“浏览器 → 本机程序 → 模型服务商”的数据流，核对服务商留存，不把本地不存储写成全链路不留存。
- [ ] 两个独立浏览器会话手工测试隔离；清除后输入“刚才我说了什么”，确认不会调用旧上下文。
- [ ] 将 CLI 改为复用页面使用的会话逻辑，验证两种入口的清除效果一致；不会在新会话中恢复旧的安全状态或私人信息。
- [ ] 运行 python -m pytest tests/test_session_privacy.py -q；预期全部通过。运行 python -m streamlit run app.py --server.address 127.0.0.1；预期只在本机演示。
- [ ] 更新启动说明、用量统计和隐私说明；不为原型配置公开访问地址。

**验收：**说明与行为一致；页面能使用，开发者能检查动作与来源，但没有私人信息进入常规日志。

### Task 7：独立评测与问题分类（第 7 周）

**Files:** 创建 scripts/evaluate.py、tests/test_eval_split.py、docs/evaluation-rubric.md、reports/baseline/；冻结 data/eval/holdout.jsonl。

**Interfaces:** evaluate(cases_path: Path, output_dir: Path, gateway: ModelGateway) -> dict；报告至少包含案例 ID、gateway_mode（mock/live）、模型/提示词/知识版本、预期与实际动作、人工意见、错误类型、调用次数、用量、耗时及未运行项。mock 报告只列程序行为，模型识别效果、回复质量和实际费用均标记 not_evaluated，不输出虚构的能力指标。

- [ ] 校验并冻结从第 2 周起另外准备的 40 个保留案例，检查与 80 个开发案例没有家族交叉；不足则安排额外编写时间，不减少覆盖类别，也不把“2 小时冻结整理”当成全部编写工作。
- [ ] 写 test_scenario_family_disjoint、test_report_does_not_convert_missing_usage_to_zero、test_model_judge_is_not_clinical_approval、test_mock_report_has_no_model_performance_claim；实现评测入口与格式检查。
- [ ] 先跑开发集检查运行，再跑保留集；安全相关多轮案例各重复 3 次，报告每次结果，观察生成的不稳定性。
- [ ] 请专业人员独立检查完整多轮记录；尚未请到时由开发者进行技术检查，并把“专业审核未完成”写在结论中。
- [ ] 将问题分为 P0 严重安全/隐私/虚假救援问题、P1 重要错误建议或流程失效、P2 表达/相关性问题；分级是本项目工程规则，不是医学风险分层。
- [ ] 运行 python -m pytest tests/test_eval_split.py -q；预期分组检查通过。运行 python -m scripts.evaluate --cases data/eval/holdout.jsonl --out reports/baseline；预期生成逐例报告和汇总。
- [ ] 每个缺陷记录复现步骤、影响、负责人、修复计划和回归案例；不以单一总准确率作结论。

**验收：**报告能定位具体问题；独立性、样本规模和专业审核缺失都公开记录，没有把合成测试分数当临床效果。

### Task 8：修复、复现与下一阶段审查（第 8 周）

**Files:** 修改受缺陷影响的模块与 tests/；创建 reports/v0.1/、docs/pilot-readiness.md、docs/demo-script.md；完善 README.md。

**Interfaces:** 不增加核心模块接口；接口若必须变化，统一更新所有调用方、测试和本计划的接口约定。

- [ ] 优先修复 P0/P1；每个真实缺陷先加入能复现它的测试或评测案例，再修复，再验证。
- [ ] 被用来修复的保留案例转入回归集，并补充独立保留案例；报告保留集的变化原因，不能继续声称它从未用于开发。
- [ ] 运行 python -m pytest -m "not live" -q；预期全部离线测试通过；只对受变更影响的模型场景和重要安全场景进行针对性重测。
- [ ] 在 live 模式记录 20 个代表性虚构会话的调用量、错误、耗时和实际账单估算，说明样本限制；核对 4 次/20 秒/45 秒限制是否生效。只有 mock 时仅验证限制与统计格式，实际成本、模型延迟保持未评测。
- [ ] 在新建虚拟环境中按 README 安装锁定依赖，完成模拟模式演示；模型接入版还必须完成真实 API 演示与保留集评测。没有 API 时明确只交付离线工程框架。
- [ ] 准备 5 段演示：倾诉、需要追问、查知识、需要专业评估、模型失败后的备用回复；安全相关演示使用虚构案例。
- [ ] 完成试用条件表：满足/未满足/证据；没有专业审核就保留为研究演示，不能让日期自动触发上线。
- [ ] 保存 v0.1 版本、已知限制和后续优先级。完成标记的依据是报告和实测结果，不是代码已经写完。

**验收：**对应 A/B 交付级别的结果可复现，严重已知缺陷没有未处理项；如果还有未解决的严重缺陷，交付问题报告并保持相应验收未完成。文档完成、程序完成、真实模型评测完成、专业审核完成分别记录。

## 九、Review Focus

| 最可能影响用户的输入或条件 | 期望行为 | 负责的任务与验证 |
|---|---|---|
| 安全线索在多轮后期出现，前面一直像普通倾诉 | 每轮重新评估并及时改变动作，不能被旧标签锁死 | Task 4 的 test_new_turn_can_escalate；Task 7 的多轮人工评审 |
| 模型 JSON 缺字段、矛盾、超时或检查器失败 | 保留未知/失败，使用对应备用回复，不宣称安全 | Task 3 的无效 JSON 测试；Task 5 的检查器故障测试 |
| 用户引用他人、否认、使用隐晦表达，或陈述异常感知体验 | 区分主体与时间；不擅自确诊、不附和异常信念，必要时澄清与专业求助 | Task 3 的引用证据测试；Task 4/7 的情境评测 |
| 检索到未授权、未审核或夹带指令的资料 | 过滤不合格内容；资料只能作为内容来源，不能覆盖系统策略 | Task 2 的来源校验；Task 5 的资料与注入测试 |
| 会话清除、两个用户并行、供应商保留数据 | 无跨会话泄露；本地清除有效；服务商留存如实说明 | Task 6 的隐私测试、手工隔离检查与数据流记录 |

## 十、如何评估，而不是只看回答像不像人

| 维度 | 记录什么 | 通过或处理方式 |
|---|---|---|
| 程序正确性 | 规则、解析、隔离、清除、预算和超时测试 | 已定义的确定性测试全部通过；失败必须修复 |
| 事实忠实度 | 凭空添加症状、时间、经历或证据的次数 | 逐例检查，关键事实错误进入缺陷清单 |
| 安全线索发现 | 需要安全支持却遗漏的案例、误报案例和发生轮次 | 分开报告漏检与误报，包含分母和具体情境 |
| 回应质量 | 共情、是否回应需求、提问负担、建议适用性 | 人工按统一量表打分并写依据；模型评分仅作辅助 |
| 医学边界 | 确诊、用药调整、许诺疗效、虚假转介、强化异常信念 | 严重问题没有未解决项；真实用户前需要专业审核 |
| 知识依据 | 来源是否实际支持回答、来源是否伪造 | 不支持的医学主张不能因为语气自然而放行 |
| 稳定性 | 同一安全案例重复 3 次的表现、失败恢复 | 不一致结果记录并分析，不只挑最好的一次 |
| 成本与速度 | 每轮实际调用数、token 用量、耗时、失败重试 | 和自己设定的预算比较；没有用量就标未知 |

不设置未经验证的“诊断准确率 95%”“低分即安全”等目标。即使有限测试里没有发现严重问题，也不代表已经证明对真实用户安全或有效。WHO 建议医疗生成式 AI 明确任务、让专业人员和使用者参与，并验证部署表现；本计划的具体测试与数量是工程建议。[WHO 指南说明](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models)

## 十一、成本与人员安排

| 项目 | 首阶段安排 | 控制方式 |
|---|---|---|
| 开发设备 | 使用现有电脑运行程序，模型通过 API 调用 | 无须为首版预先购买 GPU |
| 模型 API | 第 1 周按服务商实时价格估算，自己确定月度封顶 | 能设置服务端额度就设置；程序统计失败和多次调用 |
| 文档/资料授权 | 优先使用权限清楚、适合本用途的资料 | 申请授权未完成时不纳入产品资料包 |
| 专业审核 | 从第 2 周接洽，单独预算和排期 | 技术工作量 80～96 小时不包含专业人员工作时间 |
| 服务器 | 8 周原型本地运行 | 真实用户阶段才按实际架构另行估算 |

成本估算公式：月模型费用 ≈ 会话数量 × 每会话轮数 × 每轮各次请求的平均费用总和。每次请求费用按输入/输出 token 和供应商实际计费项目计算，重试、缓存、工具或检索等额外收费也要计入。先实测 20 个虚构会话再估算，不直接套用网上的每次聊天价格。

你的主要工作是场景定义、资料整理、学习关键代码和验收体验；实现者负责程序与测试；专业人员负责内容适用性、安全流程和真实用户阶段的专业审查。这些角色不能互相冒充。

## 十二、研究原型之后的工作计划

### 阶段 B：专业审核与受监督试用准备

时间可先预留 4～8 周以上，但由审核、合作和缺陷决定，不作为保证工期。

- [ ] 指定专业负责人，明确服务内容与医疗诊断边界。
- [ ] 确定实际用户地区、人群、招募方式和需要的伦理/合规流程。
- [ ] 审核全部安全相关策略、备用文案、求助资源和关键知识卡。
- [ ] 选择正式数据处理方案，落实最小收集、知情同意、权限、保存期限、删除和供应商条款；涉及跨境另行核查。
- [ ] 如果部署给多人使用，增加身份验证、访问隔离、加密、限流和异常监测，并完成相应测试；本地 Streamlit 演示不能直接视为生产系统。
- [ ] 设置能够实际执行的人工求助与异常事件流程，明确工作时段、责任和暂停条件。
- [ ] 由专业团队决定试用人群和人数；先做受监督的可用性观察，不能通过招募危机用户来“测试安全性”。
- [ ] 发生严重误导、隐私事件或处置流程失效时暂停，记录、复核并修复后再决定是否恢复。

只有上述条件满足才开始真实用户试用。请不到专业人员时，继续做虚构案例研究，不把朋友随便试聊当作专业审核的替代。

### 阶段 C：根据证据决定产品化方向

试用后先回答：目标用户是否需要、能否持续提供合适帮助、主要失败是什么、成本是否可承受。再决定是否增加长期记忆、量表、更多困扰范围或升级检索。

微调只在已有清楚授权的数据、明确可重复的问题和有效评测后考虑；语气更像咨询师不能证明临床有效。若要作诊断或治疗效果声明，需要另外设计有专业监督、适当伦理审查的临床验证工作。

## 十三、遇到阻碍时怎么继续

| 阻碍 | 继续推进的办法 |
|---|---|
| 还没有 API 或支付条件 | 用 FakeGateway 先做界面、流程、数据和确定性测试；如实标注没有完成真实模型评测 |
| 没拿到公开数据集授权 | 使用自己编写的虚构案例；不复制受限数据进入产品资料 |
| 找不到专业审核人员 | 交付技术研究原型和审核待办，真实用户阶段保持未启动 |
| 检索效果不好 | 先检查标签、知识缺口和查询表达，再决定是否需要向量检索 |
| 代码量超过学习能力 | 缩减界面功能，保持一个模型、一套流程、少量知识卡；不要同时引入多个框架 |
| 模型在关键情境持续失败 | 暂停扩大功能，检查状态提取、策略与备用流程；必要时重新选择模型并重跑关键评测 |
| 时间不够 | 保留任务依赖与验收，顺延时间；优先削减外观、账号和长期记忆等非核心功能 |

## 十四、工作记录模板

每周保留一页：本周交付物链接；完成/未完成的验收；失败案例；数据与提示词版本；调用花费；专业审核状态；下周最多 3 个优先事项。

每日按“完成一个可运行的小功能 → 检查具体行为 → 记下问题”推进。不要以写了多少代码、下载了多少数据作为完成标准。

## 十五、参考资料

- Python 虚拟环境：[官方 venv 文档](https://docs.python.org/3.12/library/venv.html)。
- 本地页面：[Streamlit 安装文档](https://docs.streamlit.io/get-started/installation)。
- 结构化数据校验：[Pydantic 官方文档](https://docs.pydantic.dev/latest/)。
- 自动化测试：[pytest 入门](https://docs.pytest.org/en/stable/getting-started.html)。
- 法律与医疗边界：[《精神卫生法》](https://www.nhc.gov.cn/fzs/c100048/201808/5d03e37b37c944b08d701a0b5722160a.shtml)、[《个人信息保护法》](https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm)。
- 安全评估边界：[NICE 自伤指南](https://www.nice.org.uk/guidance/ng225/chapter/recommendations#risk-assessment-tools-and-scales)。
- 医疗 AI 评估与治理：[WHO 指南说明](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models)。

资料与接口在执行时应核对当前版本。本文是具体工作安排，不能替代专业内容审核、法律适用判断或临床验证。
