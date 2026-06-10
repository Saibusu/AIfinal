# tests/ — 測試

| 路徑 | 用途 | 執行環境 |
|------|------|---------|
| `test_*.py` | 單元測試 + 屬性測試（覆蓋率 ≥ 90% on src/）| hosted runner |
| `integration/` | 需真實 Yahboom (Jetson) 硬體的端到端測試 | self-hosted Jetson runner |

## 五大測試類別（對應課程 §B.5）

1. 推論邏輯單元測試（模型載入、輸出 shape、決策邊界）
2. 訊息單元測試（MQTT publish/subscribe、JSON schema）
3. Accuracy gate（held-out set mAP vs `accuracy_baseline.json`）
4. 整合測試（真實 Jetson，camera + 推論 + LED）
5. Coverage gate（`--cov-fail-under=90`）

GPIO 在單元測試中以 `unittest.mock` 替代（見 SPEC-002）。
