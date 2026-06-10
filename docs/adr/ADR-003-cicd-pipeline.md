# ADR-003 — CI/CD Pipeline 架構

| 欄位 | 內容 |
|------|------|
| **Status** | Draft |
| **Date** | 2026-06-11 |
| **Authors** | 李軒杰 (I4A70), 黃義鈞 (I4B58) |

---

## 背景 (Context)

課程要求 5-stage CI/CD pipeline（佔 5 分），且 integration-test 必須在
self-hosted Jetson runner 上執行。GitHub Actions on public repo 提供免費 CI。

---

## 決策 (Decision)

**實作課程規定的 5-stage DAG，搭配 self-hosted Yahboom (Jetson) runner。**

```
lint ──┬──▶ test (coverage ≥ 90%) ──┐
       │                             ├──▶ build ──▶ integration-test
       └──▶ security-scan ───────────┘
```

---

## Pipeline 設計

### Stage 1: lint
- Runner: ubuntu-latest（hosted）
- 工具：`ruff check src/ tests/`
- 通過條件：零違規

### Stage 2: test
- Runner: ubuntu-latest（hosted）
- 工具：`pdm run pytest --cov=src --cov-fail-under=90`
- 通過條件：覆蓋率 ≥ 90%，所有單元測試通過
- GPIO Mock：使用 `unittest.mock` 替代 `Jetson.GPIO`

### Stage 3: security-scan
- Runner: ubuntu-latest（hosted）
- 工具：`bandit -r src/` + `pip-audit`
- 通過條件：零高嚴重性發現

### Stage 4: build
- Runner: ubuntu-latest（hosted）
- 工具：`docker buildx build --platform linux/arm64`
- 推送：`ghcr.io/saibusu/aifinal:sha-<commit>` + `:latest`
- 注意：TensorRT engine 編譯在 entrypoint，不在 build 階段

### Stage 5: integration-test
- Runner: `[self-hosted, linux, arm64, jetson]`（Yahboom 套裝）
- 流程：pull image → start container → run `tests/integration/`
- 測試：camera + 推論 + GPIO LED 實際觸發

---

## 部署流程（tag-triggered）

```
git tag v1.0.0 → deploy.yml 觸發 → 需人工 approve → deploy.sh on Jetson
```

---

## 理由 (Rationale)

1. **課程規範對齊**：完全符合 §B.4 五階段要求
2. **GPU 工作分離**：TensorRT 編譯需要 GPU，不可在 hosted runner 執行
3. **PDM 管理**：與課程 HW6 一致，grader 直接執行 `pdm install`
4. **GHCR**：GitHub Container Registry 免費，arm64 image 可直接在 Jetson 拉取

---

## 後果 (Consequences)

**正面：**
- 每次 push 自動驗證程式碼品質與安全性
- integration-test 在真實硬體上確保 GPIO + 推論正常

**負面：**
- Self-hosted runner 需要 Yahboom 持續開機（或手動啟動）
- arm64 cross-build 可能較慢（5–10 分鐘）

---

## 驗收條件 (Done When)

- [ ] `.github/workflows/ci.yml` 包含五個 stage
- [ ] GitHub repo Settings → Actions → Runners 顯示 Yahboom runner 為 Idle
- [ ] `main` 最新 CI run 五個 stage 全綠
- [ ] GHCR 有 `:latest` 和 `:sha-<commit>` 兩個 tag

---

> **注意**：Status 為 Draft，未經人類核准前不得有對應生產代碼。
