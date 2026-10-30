# 心理小测试扩充实施计划

规格：[design](../specs/2026-10-30-expanded-questionnaires-design.md)。用户已要求将先前检索的测试加入现有流程，直接实施已核实的项目。

1. 并行核实/实现题本：IPIP100；SCS26/12与MAAS15；ECR-R36/RS9及DOSPERT30。每组独占新模块与计分键回归，不修改注册表。来源只用作者/出版社，中文自译和实际许可登记。
2. 给Questionnaire追加显式composites、show_dimensions、context_options；QuestionnaireResult追加composites。先用不等长分维独立样本证明总体等权，再实现并检查原问卷不改变分数。
3. 注册7个新版本，启用新入口并保持版本身份和原有记录；关系选项从定义读取，原12题保留现状。SCS12只展示总体，SCS26六维加总体；导出与界面一致，其他新构念使用单独解读。
4. 执行有意义的目录/逐题/结果/版本和关系隔离回归；完整pytest与check_data；浏览器核对新题目和图表。独立审查，更新资料和执行记录，源码清单校验后同步GitHub。

重点：SCS总分不能按26题直接平均；短版不输出六维画像；MAAS锚点方向；ECR36不要套IRT排序键或原创类型阈值；DOSPERT仅行为意向且五领域独立；ECRRS对象切换不混合原始答案与结果。
