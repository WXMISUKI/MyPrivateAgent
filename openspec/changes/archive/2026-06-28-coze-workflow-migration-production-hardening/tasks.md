## 1. Dependency Mapping Contract

- [x] 1.1 统一 workflow registry 的依赖映射输出，把 Coze 节点分类收口为 `runtime_capability`、`provider_backed`、`artifact_input`、`explicit_blocker`
- [x] 1.2 补齐 blocker 语义字段，让未支持节点、未注册 provider、缺失 artifact 输入都能返回机器可读原因
- [x] 1.3 让 Workflow Lab 详情页和回放结果直接展示 dependency mapping contract，而不是仅展示文本摘要
- [x] 1.4 增加后端聚焦测试，覆盖 `http.request`、文件输入、provider-backed capability、unsupported node 四类映射

## 2. Workflow Invoke Hardening

- [x] 2.1 统一工作流对外 capability id 与 invoke envelope，确保返回 `workflow_id`、`capability_id`、`workflow_version`、`run_id`、`status`、`authorization`、`invocation_policy`、`trace_summary`
- [x] 2.2 确保 `POST /api/coze-workflows/{workflow_id}/invoke` 与 `POST /api/capabilities/{capability_id}/invoke` 复用同一条 production envelope
- [x] 2.3 为 draft / review workflow 增加 fail-closed 行为，明确不可作为 production callable capability 暴露
- [x] 2.4 为 readiness、ownership、policy failure 增加错误路径测试，验证 invocation 不会绕过 capability runtime

## 3. Docs and Acceptance Evidence

- [x] 3.1 更新 `docs/guides/coze_migration_workflow_authoring.md`，把新的 dependency mapping分类和 fail-closed 规则写成协作规范
- [x] 3.2 更新 `docs/guides/coze_workflow_lab_verification_runbook.md`，补充稳定 invoke envelope、blocker 分类和验收步骤
- [x] 3.3 为至少一个正式样例补充 `docs/integration/...-launch-acceptance.md`，记录输入、输出、边界和 replay 结果
- [x] 3.4 同步更新 `docs/guides/capability_runtime_registry.md` 和 `docs/architecture/runtime_contracts.md`，保持 contract 真源一致

## 4. Validation and Archive

- [x] 4.1 运行 OpenSpec 校验，确认 change 通过 `openspec validate --strict`
- [x] 4.2 运行后端聚焦测试，确认 registry、lab、invoke hardening 相关用例通过
- [x] 4.3 如有前端展示变更，运行 Workflow Lab 聚焦测试并确认只读回放仍可用
- [x] 4.4 验证通过后归档 change，并保留 docs 里的上线验收记录作为迁移样板
