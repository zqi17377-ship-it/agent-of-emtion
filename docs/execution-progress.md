# Execution ledger — plan: docs/superpowers/plans/2026-10-22-mental-support-agent-work-plan.md

Started: 2026-10-29. User authorized execution and selected DeepSeek.

## Rulings and preflight

- Ruling: This directory has no Git repository or existing product code; implement in the named workspace, preserve planning files, and keep this durable ledger instead of Git-dependent skill scripts. No commit or worktree is claimed.
- Ruling: Python 3.13.5 is installed rather than 3.12. Verify compatibility on 3.13 and record it; do not install another interpreter without need.
- Ruling: venv ensurepip fails because the sandbox temporary directory denies writes. Use a project venv with system-site-packages and without pip, plus a tested dependency snapshot. This is not proof of a fresh-machine installation.
- Ruling: User selected DeepSeek; implement its documented chat API behind the gateway. No key is requested in chat, no private messages are sent during development.
- Pre-flight 1→3→5: trusted instructions, normalized errors and one shared request budget flow through assessment, generation and checker.
- Pre-flight 2→5→7: provenance, permitted purpose and professional review are different states; synthetic materials remain professionally unreviewed.
- Pre-flight 3→4→5: evidence IDs and unresolved signals survive turns; unknown or failed assessment cannot clear them.
- Pre-flight 5→6: CLI and page share session/workflow, and clear erases all state.
- Pre-flight 7→8: mock evaluation verifies software only; live quality, costs, independent professional review remain incomplete without evidence.

## Status

- Task 1: offline implementation verified — five initial RED failures became GREEN; DeepSeek documented transport, normalized errors, key protection, request caps, CLI and config are implemented. Real API and budget/account terms remain pending.
- Task 2: draft assets created — 40 original support cards, 80 dev and 40 holdout synthetic cases. validate_assets passes; license/source/family regressions fail before implementation then pass. Professional review pending; author-visible cases are not independent clinical labels.
- Task 3: structural/evidence validation implemented — initial missing-module RED tests became GREEN; unknown, quoted speech, denial, invalid JSON and invented duration regressions included. Live extraction untested.
- Task 4: action rules implemented — urgency survives topic change/failure/denial, original evidence preserved, context correction audited. Two additional RED regressions found and fixed missing historical evidence and unrelated quoted context clearing urgency. Professional review pending.
- Task 5: workflow implemented — knowledge filtering, output checking, fail-closed fallback and shared budgets. Normal paths, bad checker, missing source, injection placement and overflow covered by offline tests. No medical efficacy validation.
- Task 6: page and CLI implemented — Streamlit AppTest verifies consent gate, a mock conversation and clear; independent session and secret-free logging tests pass. Only localhost configuration.
- Task 7: mock evaluation completed — 80 dev cases /108 runs and 40 holdout cases /52 runs, including repeated safety-category cases and synthetic transport faults. All model-quality/actual-cost claims remain not_evaluated; professional review pending.
- Task 8: offline handoff package prepared — README, startup, dependency snapshot (49 installed packages), data/response/privacy/evaluation documentation, and disabled real-user pilot checklist. Fresh-machine install, live billing/latency and professional approval remain pending.

## Further rulings

- Ruling: User selection of DeepSeek replaces the plan's two-provider selection exercise. Default model name is deepseek-flash per official documentation checked 2026-10-29; no legacy model availability is assumed.
- Ruling: Do not claim authorization or expert approval for third-party material. Populate original AI-assisted draft texts and explicit pending review metadata, and keep eligible_pilot blocked. Cost if insufficient: clinical content and independent validation are still required before human trial.
- Ruling: Windows sandbox blocks asyncio's self-pipe in socket.accept (captured with pytest faulthandler). Use synchronous HTTPX in a daemon request worker with a bounded Future wait and per-I/O timeout. Requests may continue remotely after local timeout; do not imply cancellation or free billing.
- Ruling: Persist historical Evidence with Decision as well as IDs; otherwise a later model cannot reconstruct why a signal was retained. These records remain in session memory and clear with the conversation.
- Ruling: Add per-turn metrics to TurnResult so synthetic evaluation can retain attempt counts and unknown usage without logging raw conversations.

## Verification so far

- Python 3.13.5; Pydantic 2.13.5; HTTPX 0.28.1; Streamlit 1.63.0; pytest 9.1.1.
- python -m pytest -q → 51 passed in 3.54s (before final independent review).
- python -m scripts.check_data → valid=true, errors=[].
- Model transport has been exercised with MockTransport only. No credentials printed, no live requests made.
- Independent final code review completed; findings and final fix evidence follow below.

## Final independent review and fix pass

The reviewer reproduced four important findings; all were verified with failing regressions before repair:

- Final: fixed failed assessments clearing urgency — test_failed_assessment_cannot_apply_quoted_correction RED→GREEN. Failed assessments cannot change prior signals/evidence.
- Final: fixed stale/unrelated same-kind quotes resolving an urgent signal — test_stale_quoted_evidence_cannot_clear_later_urgency and test_unrelated_same_kind_quoted_signal_cannot_clear_urgency RED→GREEN. Evidence now has a program-assigned message_index, with chronological checks and same-signal association.
- Final: fixed uncertain signals preventing later confirmation from escalating — test_uncertain_urgent_signal_can_be_confirmed RED→GREEN.
- Final: fixed incomplete usage appearing as complete numeric totals — test_missing_usage_after_success_makes_aggregate_unknown RED→GREEN for one and two failed/missing attempts. Unknown totals remain unknown after further successful attempts.
- Final suite: python -m pytest -q → 57 passed in 4.18s. Streamlit AppTest includes a mock conversation and clearing the visible history. Data validation valid=true; baseline regenerated in mock mode.
- Final: minor (deferred): check_data case validation can be strengthened to require every case ID/message/expected-action field, beyond current field/source/group checks. Current bundled drafts are complete; malformed future input may fail with an ordinary script error. No clinical-quality score is inferred.
- Final: Ruling: live DeepSeek behavior/quality, actual charges, fresh-machine installation, clinical suitability and real-user readiness require external evidence and remain explicitly pending. Cost if skipped: this package cannot support model efficacy, billing, or human-trial claims.
- Final: Ruling: localhost demonstration server startup is reversible and implied by executing the local-app plan. It runs offline by default on 127.0.0.1:8501; no account credentials or model calls are needed to view it.

No Git commits, professional sign-off, or live model test is claimed. Plan completion is limited to grade A engineering delivery, with grade B/C gates still open in implementation-status.md and pilot-readiness.md.

## Local handoff

- The local-only server is running on http://127.0.0.1:8501 (exec session 74511).
- Health endpoint verified outside the sandbox's loopback restriction: HTTP 200, body ok.
- reports/development and reports/baseline were regenerated after fixes, including prompt/policy/knowledge/case SHA-256 manifests. No model-performance or actual-cost claims are generated for mock runs.
- Deferred external steps and the one minor validator improvement are visible in this ledger; no hidden approval or medical completion is inferred.

## User API configuration follow-up — 2026-10-29

- User confirmed local API configuration completed. Ran one fixed synthetic-case live smoke test, requiring no secret output.
- Added scripts/live_smoke.py with two RED→GREEN regressions: fallback is never reported as success; mock completion is not reported as real API success.
- Live result: assessment/response/check all ok, 3 requests, total 5392 ms, reported input/output 3660/227 tokens. Report reports/live/smoke-5f3cf42d.json contains only fixed synthetic-case output and normalized metrics.
- Full suite: 59 passed in 4.18s. Local page health: HTTP 200, body ok.
- B-stage broad quality, expert review, actual billing and human-trial readiness remain pending; earlier no-live statements above describe the earlier offline delivery state.

## v0.2 UI and functionality — 2026-10-29

- User requested UI redesign and continued functionality, then said continue. Retained Python/Streamlit and original research constraints; scope and tasks recorded in 2026-10-29-chat-experience design/plan.
- Configuration refresh reproduced with failing temporary-file tests; pure fresh reads and safe readiness now pass 16 tests, without mutating process environment or printing credentials.
- Root completed workspace and dialogue changes after a prior helper could not finish. Memory-only conversations, explicit downloads and feedback add no automatic persistence or network requests.
- AppTest RED missing controls became GREEN after UI refactor. Real narrow browser confirmed homepage, starter prefill without send, confirmation enabling input, feedback, and mode switch preserving old chat.
- Independent read-only review found rejected-turn metadata overwrite/hidden message. Two regressions were watched fail then pass after guarding attachment and displaying unattached results.
- Full suite after fixes: 93 passed in 6.29s. No new dependencies or public deployment.
- Ruling: User's continue instruction authorizes implementation of the stated revision; visual choices default to warm ivory/sage and clear controls. No additional approval loop was introduced for reversible local edits.
- Ruling: multi-conversation data and feedback stay in browser-session memory; explicit transcript export is the only download. Actual user's medical data was not used for verification.
- Browser finish: verified desktop and original narrow viewport, corrected double composer spacing so the desktop brand no longer scrolls behind the header. Saved three JPEG screenshots under docs/screenshots and reset viewport override.
- Two-turn real DeepSeek verification used only fixed synthetic input, maintained listen action, and responded to the new contextual detail. Final browser returned to a fresh chat with consent boxes unchecked; no actual user health data or credentials appear in screenshots.

## v0.3 psychological exploration — 2026-10-29

- 用户先要求从聊天观察类似 MBTI 的性格，随后明确加入依恋倾向与更多测试。最终顶栏“心理探索”包含七工具：MBTI 风格对话观察（附八题原创自述）、依恋原创 12 题、Mini-IPIP 20 题、TIPI 10 题、RSES 10 题、应对信心原创 6 题、SWLS 5 题。设计和计划已按最终范围更新。
- 实际状态类为 `ExplorationState`，位于 `support_agent/exploration_state.py`，归属于每个 `Conversation`；未采用早期计划中的 `PersonalityState` / `personality_state.py`。六问卷采用统一完整作答及正反向计分，各维分别展示，不合成大五人格总分或概率。
- 六问卷、八题自述与自我确认均本机处理，不自动发给模型。对话分析仅在 DeepSeek 配置、研究范围、API 数据流向及费用确认、至少两段用户消息和单独分析同意满足后，通过主动按钮触发；每次最多两次请求，共享 40 秒截止时间。连接区的费用文案已覆盖主动性格分析。
- 独立审查复现了自报四字母标签被按单个字母引用后误当四维支持的问题；已修复标签位置与片段过滤并增加回归。原话校验确认引用属于用户且逐字一致，不证明语义推测正确。未知/矛盾保留，失败分析不覆盖已有观察，对话更新提示旧结果。
- 独立 AppTest 检查中将配置就绪函数预先替换并禁止模型调用，未读取本机密钥：切换依恋关系后十二题为空，旧结果仍保留旧关系标签；单独清除探索记录后结果、答案控件及关系选择清空；新对话不继承探索数据。单独报告不包含内部指纹或 API 配置。
- 来源与范围按实际题库记录：依恋和应对信心为未经验证的原创题，不是 ECR-R/ECR-RS 或 GSE；Mini-IPIP、TIPI、RSES、SWLS 为未经中文信效度验证的项目研究自译。IPIP、RSES 公共领域声明及 TIPI 作者许可保留署名；SWLS 明确仅非商业研究，不推定商业授权。详细出处和计分见 [psychological-tools.md](psychological-tools.md)。
- 最终完整回归：`python -m pytest -q` → **226 passed in 13.31s**。该记录验证软件行为，不构成临床效用或心理测量有效性评估。
- 实际 DeepSeek 验证仅使用两段虚构成年人的日常偏好，一次请求返回 `status=ok`、四轴 `supported`，全部引用通过字面原话校验。未使用真实用户健康材料；未将单例接通结果当作人格准确性或实际账单验证。
- 实际浏览器完成研究确认、七工具目录检查、SWLS 五题全部中项并计算为 **20/35**，结果导出按钮可见；未发送的虚构聊天草稿在进入探索、换工具、计分和返回聊天后均保留。AppTest 的 `ChatInput.value` 是测试接口的临时值，草稿保留结论依据实际浏览器检查。未声称已验证全部浏览器下载文件内容。
- 截图：[七工具目录](screenshots/v03-exploration-catalog.jpg)、[窄屏 SWLS 结果](screenshots/v03-swls-result.jpg)。完整验证记录见 [v03-verification.md](v03-verification.md)。README、工具说明、设计和计划已更新。
- 本轮继续限于本地、非商业、成年人虚构案例研究；专业审核、中文信效度、独立人格准确性研究和真实用户试用仍待完成。无新依赖、公开部署、Git 提交或专业签字。

## 多题数版本与对话探索制作方案 — 2026-10-29

- 用户要求同一主题的不同题数版本，并请求对话达到一定量后探索MBTI风格、性格和亲密/人际关系依恋的制作方案。已保存独立设计建议稿与六项制作任务；自动功能与新问卷版本尚未接入。
- 一手来源核实了TIPI10/Mini-IPIP20/IPIP50和100、BFI-2正式15/30/60、ECR-RS每关系9/ECR-S12/ECR-R36及SWLS3/5，明确不同工具不等于可随意截取的同一量表，许可与中文验证须按版本核对。
- 用户进一步授权使用已配置API，并选择优化现有DeepSeek提示词和效果。只创建独立候选提示词、三组合成seed和可重复评测脚本，不使用真实心理对话、不训练模型权重。
- 实际请求严格3次、无重试：2组满足预设检查，1组未输出预期大五条目。冻结报告总体failed；预期本身也需人工复核，不强迫模型从EI推导大五，不报告准确率或基线提升。输入4,708、输出563 tokens。详情见[首次提示词试测记录](conversation-observation-prompt-evaluation.md)。
- 独立制作方案审查提出5项契约补强，已纳入：手动/自动/修复共享原子预算；单条删除和修正也使迟到任务失效；版本身份贯穿控件/结果/导出；会话内匿名关系对象；主题授权约束实际请求。另明确字符上限先于20条时的退化路径。
- 根代理无网络重跑dry-run退出0，参考输出与错误变体检查通过；live报告哈希保持不变。现有应用产品代码未因本轮变动。
- 本轮最终现有应用回归：`python -m pytest -q`，退出0，226 passed in 13.21s；不将其作为尚未实施的自动功能验收结果。

## v0.5 分步使用流程 — 2026-10-30

- 按用户明确要求将首次使用入口、聊天准备、问卷、性格问答和对话观察设置拆为顺序页面；共享步骤标题、进度、持久草稿与同意状态。问卷逐题作答、核对后提交，结果单独展示。
- 完成首页三入口、聊天三步、观察五步；关系对象管理与逐消息标注各自独立。修复退出人格连接设置后错误跳转，并以先失败后通过的回归验证。
- 最终完整软件回归313 passed in39.03s，数据检查valid true。实际浏览器验证SWLS3中项12/21、返回保留答案、IPIP50单题展示、聊天与观察分步。观察设置后额外请求0/6，本轮没有模型API请求。
- 研究、许可与测量限制沿用既有说明，不将界面测试解释为心理诊断或人格准确性验证。详见[v0.5说明](v05-release.md)。

## v0.5.1 API-only — 2026-10-30

- 用户明确要求移除离线演示，后续模型效果验证直接使用API。产品与CLI统一DeepSeek；移除选择模式页，聊天准备缩为研究范围与连接/发送费用确认两步。缺配置时禁发，工厂不再返回演示gateway。
- 固定输出替身只留在tests用于可重复的纯软件回归，模型链路以真实API验证。批量合成评测默认限制3案例/12请求，可进一步收紧。
- 审查复现旧agent_session演示历史被默认live重标的问题，先失败回归后修复；原历史保持只读并可新建API对话，不隐式混用。
- 最终完整回归322 passed in44.90s；数据检查valid true。实际浏览器两步准备后发送一个固定虚构案例，status ok/action listen，3请求，5,042ms，输入/输出3708/201 tokens；观察关闭。截图仅本地保存。没有新增模型准确性或临床有效性结论。

## v0.5.2 命名与结果图形 — 2026-10-30

- 用户要求API任务完成后加入对话自行命名、选项展开、相应解读与五边形评分图。API版先提交0d6a781；随后完成手动命名持久优先、radio逐题选择、大五雷达与其他原始量程图、本机解读与导出。
- 新增纯展示模块；原题库范围和反向计分不变。审查修复依恋文字/参考边界不一致；浏览器排查确认st.html过滤SVG后，改用st.image并加入实际图片proto回归。
- 最终软件回归351 passed in47.70s，数据检查valid true。实际浏览器命名后真实API回复保留名字，3请求/5938ms/3505输入与176输出tokens；另完成TIPI10雷达及SWLS3横图/12分，问卷未调用API。详见[v0.5.2说明](v052-release.md)。

## v0.5.3 会话API设置与探索聊天入口 — 2026-10-30

- 按用户要求增加独立API设置页：每位访问者填自己的DeepSeek密钥和模型，仅当前网页会话服务端内存持有；网页所有模型路径明确传入配置快照，不读取部署者.env。CLI配置机制保留。
- 支持保存、一次连接测试、清除和回到原步骤；保存不发请求。更改/清除撤回发送及观察同意、使旧任务失效，保留消息/结果/已花费预算。错误与导出不含密钥。
- 按追加要求，五步对话探索最终确认后直接进入聊天，仍可从聊天打开设置和报告。手动/自动两种根页面回归覆盖，无消息时导航不创建gateway。
- 浏览器复现密钥控件仅清后端仍残留遮罩值的问题；新增先失败回归后，通过变更控件identity和清除form修复。实际浏览器验证保存和带未保存草稿的清除后输入均为空。
- 最终完整回归388 passed in53.01s，数据检查valid true；独立审查无可操作问题。真实DeepSeek固定连接测试1请求/988ms/24输入与1输出tokens，固定虚构聊天3请求/4933ms/3797输入与218输出tokens/status ok。共4请求，未使用真实健康材料。
- 说明软件链路与会话隔离，不新增心理诊断或测量准确性结论。截图和运行记录仅本地，发布仅源码与说明。详见[v0.5.3说明](v053-release.md)。
