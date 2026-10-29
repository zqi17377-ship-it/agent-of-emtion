# 知心 v0.2 Implementation Plan

**Goal:** 改善聊天界面和常用操作，修复配置更新与倾听策略问题。

**Architecture:** 沿用 Streamlit 和共享 run_turn；新增纯内存 Workspace，配置读取与 UI 分离，静态视觉资产不包含用户数据。

**Tech Stack:** 现有 Python、Pydantic、Streamlit、pytest；不增加依赖。

**Spec:** ../specs/2026-10-29-chat-experience-design.md。

- [x] Task 1 配置：tests/test_config.py 先复现旧配置不刷新；实现纯读取与 configuration_readiness；限定官方主机，不返回密钥。
- [x] Task 2 会话：tests/test_conversations.py 先验证隔离、新建切换、完整清空、反馈校验和仅文本导出；实现 support_agent/conversations.py。
- [x] Task 3 对话：tests/test_dialogue_preferences.py 先验证 listen 不被可选未知字段覆盖，安全/专业/失败仍优先；更新 policy.py 和提示词。
- [x] Task 4 页面：重构 app.py，静态 assets/chat.css；调整 tests/test_app.py 验证公开控件的真实行为，完成 responsive UI。
- [x] Task 5 验收：全套 pytest，浏览器真实检查窄屏和桌面、反馈不触发二次请求、保存截图、更新 README 与执行记录。

验收证据：93 passed in 6.29s；浏览器中的两轮固定虚构 DeepSeek 对话均显示“先听你说”，第二轮回应了第一轮之后补充的具体情境。截图位于 docs/screenshots/v02-home-desktop.jpg、v02-home-narrow.jpg、v02-chat-narrow.jpg。视口覆盖已恢复，最终页面回到空白会话，确认项未代用户预勾选。

既有会话可能在代码热更新时需要一次迁移；不得把已有用户文本写入磁盘。导出只在用户点击下载时发生。接口接通与临床效果分别记录。
