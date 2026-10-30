# GitHub 阶段性发布

目标仓库：[zqi17377-ship-it/agent-of-emtion](https://github.com/zqi17377-ship-it/agent-of-emtion)，默认分支 `main`。2026-10-29只读核实仓库为空，认证账号具备管理与写入权限。该事实仅对应核实时点；写入前必须重新读取远程分支和提交。

阶段性提交仅包含下面明确列出的源码、提示词、文档、依赖声明、合成研究数据与测试。不上传真实 `.env`、供应商凭据、虚拟环境、会话导出、本地数据库、缓存、运行报告或内部工具目录。`.env.example` 只包含占位设置，可发布。`docs/screenshots/` 的既有图片不在本次文本源码清单中，引用这些图片的历史文档在远程可能不显示图片。

`data/` 的开发/保留案例带 `synthetic: true`，来源登记与种子脚本说明为原创合成草稿；知识卡是研究支持表达草稿，不是真实咨询记录，专业审核仍待完成。合成性与字段检查不能替代专业有效性评估，不将运行中的用户对话追加到这些文件。

发布必须等待当前产品修改和测试完成，再以最终文件内容重新生成哈希与检查清单。预检只报告疑似密钥所在文件路径，不打印匹配值；真实 `.env` 不参与读取、扫描或上传。

优先使用 GitHub 连接器。已有历史时：读取 `main` 最新SHA及树，上传清单内文件的blob，在该树上建立增量tree，以最新SHA为parent创建commit，最后以 `expected_sha` 核对并且 `force=false` 更新main。远程并发变化时重新读取和比较，禁止强推覆盖历史，也不删除清单以外远程文件。

空仓库首次提交需要特殊处理：连接器 `create_commit` 要求已有parent，不能直接创建根提交。可以先以 `create_file` 在main建立一个确定属于清单的文件（例如 `.gitignore`），读取该初始提交和tree，再按上述增量流程上传其他文件。另一方案是使用本机Git创建根提交后正常push；只能使用既有安全凭据机制，不读取或打印凭据。没有明确执行信号前不执行任何远程写入。

批量上传时每个blob只读取明确清单内文件，UTF-8解码后使用 `encoding=utf-8`；有限并发并保存每项返回SHA，只输出路径/数量/提交SHA。单项失败停止建立最终tree，不把未成功上传的清单项静默跳过。Git对象上传成功不等于分支已发布，最后必须回读main的commit/tree并核对路径、内容哈希和必要文件。

## 显式源码清单

下面清单是准备时的文件路径快照，最终提交前重新核对。扩展名白名单为 `.py/.md/.json/.jsonl/.txt/.in/.bat/.toml/.css/.example/.ini`，另外明确包含 `.gitignore/.gitattributes`；排除 `.env` 及其非example变体、`.venv/.tmp/.git/.codex/.agents/__pycache__/.pytest_cache/reports/exports/session_exports/screenshots`。

<!-- SOURCE_MANIFEST -->

```text
.env.example
.gitattributes
.gitignore
.streamlit/config.toml
README.md
app.py
assets/chat.css
data/eval/dev.jsonl
data/eval/holdout.jsonl
data/evaluation/conversation_observation_seed.jsonl
data/knowledge/cards.jsonl
data/sources.json
docs/additional-tests-research-2026-10-30.md
docs/conversation-observation-prompt-evaluation.md
docs/data-flow.md
docs/data-guide.md
docs/demo-script.md
docs/evaluation-rubric.md
docs/execution-progress.md
docs/github-publishing.md
docs/implementation-status.md
docs/live-verification.md
docs/pilot-readiness.md
docs/privacy-prototype.md
docs/provider-choice.md
docs/psychological-tools.md
docs/response-policy.md
docs/superpowers/plans/2026-10-22-mental-support-agent-work-plan.md
docs/superpowers/plans/2026-10-29-chat-experience-plan.md
docs/superpowers/plans/2026-10-29-conversational-exploration-plan.md
docs/superpowers/plans/2026-10-29-personality-exploration-plan.md
docs/superpowers/plans/2026-10-30-exploration-guidance-plan.md
docs/superpowers/plans/2026-10-30-results-and-titles-plan.md
docs/superpowers/plans/2026-10-30-session-api-settings-plan.md
docs/superpowers/specs/2026-10-22-mental-support-agent-design.md
docs/superpowers/specs/2026-10-29-chat-experience-design.md
docs/superpowers/specs/2026-10-29-conversational-exploration-design.md
docs/superpowers/specs/2026-10-29-personality-exploration-design.md
docs/superpowers/specs/2026-10-30-exploration-guidance-design.md
docs/superpowers/specs/2026-10-30-guided-flows-design.md
docs/superpowers/specs/2026-10-30-results-and-titles-design.md
docs/superpowers/specs/2026-10-30-session-api-settings-design.md
docs/v02-release.md
docs/v03-verification.md
docs/v04-progress.md
docs/v04-release.md
docs/v05-progress.md
docs/v05-release.md
docs/v051-progress.md
docs/v051-release.md
docs/v052-progress.md
docs/v052-release.md
docs/v053-release.md
docs/v054-release.md
policies/actions.json
policies/fallbacks.json
policies/help_resources.json
prompts/assess.md
prompts/check.md
prompts/conversation_observation.md
prompts/conversation_observation_runtime.md
prompts/personality.md
prompts/respond.md
pytest.ini
requirements.in
requirements.txt
scripts/__init__.py
scripts/check_data.py
scripts/eval_conversation_observation.py
scripts/evaluate.py
scripts/live_smoke.py
scripts/seed_research_data.py
start_demo.bat
support_agent/__init__.py
support_agent/api_settings_ui.py
support_agent/assessment.py
support_agent/attachment_questions.py
support_agent/cli.py
support_agent/config.py
support_agent/connection_check.py
support_agent/conversation_observation.py
support_agent/conversations.py
support_agent/exploration_catalog.py
support_agent/exploration_state.py
support_agent/exploration_ui.py
support_agent/flow_ui.py
support_agent/guardrails.py
support_agent/knowledge.py
support_agent/long_personality_tests.py
support_agent/model_client.py
support_agent/observation_jobs.py
support_agent/observation_progress.py
support_agent/observation_scheduler.py
support_agent/observation_ui.py
support_agent/onboarding_ui.py
support_agent/personality.py
support_agent/personality_questions.py
support_agent/personality_ui.py
support_agent/policy.py
support_agent/psychometrics.py
support_agent/published_personality_tests.py
support_agent/questionnaire_ui.py
support_agent/research_wellbeing_tests.py
support_agent/response.py
support_agent/schemas.py
support_agent/session.py
support_agent/session_connection.py
support_agent/survey_presentation.py
support_agent/survey_registry.py
support_agent/telemetry.py
support_agent/ui.py
support_agent/wellbeing_tests.py
support_agent/workflow.py
tests/__init__.py
tests/conftest.py
tests/helpers.py
tests/test_api_only_ui.py
tests/test_api_settings_ui.py
tests/test_app.py
tests/test_assessment.py
tests/test_cli.py
tests/test_config.py
tests/test_conversation_observation.py
tests/test_conversation_titles.py
tests/test_conversations.py
tests/test_data.py
tests/test_deadlines.py
tests/test_dialogue_preferences.py
tests/test_eval_split.py
tests/test_explicit_connection.py
tests/test_exploration_catalog.py
tests/test_exploration_guidance.py
tests/test_exploration_state.py
tests/test_exploration_ui.py
tests/test_guardrails.py
tests/test_guided_entry.py
tests/test_knowledge.py
tests/test_live_smoke.py
tests/test_model_client.py
tests/test_observation_chat_handoff.py
tests/test_observation_integration.py
tests/test_observation_jobs.py
tests/test_observation_progress.py
tests/test_observation_scheduler.py
tests/test_observation_ui.py
tests/test_observation_wizard.py
tests/test_personality.py
tests/test_personality_questions.py
tests/test_personality_wizard.py
tests/test_policy.py
tests/test_psychometrics.py
tests/test_published_personality_tests.py
tests/test_questionnaire_wizard.py
tests/test_session_connection.py
tests/test_session_privacy.py
tests/test_survey_presentation.py
tests/test_survey_registry.py
tests/test_usage.py
tests/test_wellbeing_tests.py
tests/test_workflow.py
```
