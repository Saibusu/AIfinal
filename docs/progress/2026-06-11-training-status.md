# 訓練狀態紀錄 — 2026-06-11

> 模型版本歷史與當前狀態。供 ADR-001、accuracy_baseline.json、報告 §5/§6 追溯。

## 背景：舊專案 (AI-course) 的訓練歷史

本專案模型沿用舊專案 AI-course 的訓練 notebook（已重新命名為
`notebooks/train_waste_sorter_v6.ipynb`）。舊專案的模型迭代如下：

| 版本 | mAP@50 | 狀態 | 備註 |
|------|--------|------|------|
| v1–v4 | — | 已棄 | YOLOE / TACO 路線（舊 ADR，已放棄）|
| **v5** | **0.755** | 舊 production | `best_v5.pt/onnx/engine` 存於 AI-course |
| v6 | ~0.721（epoch 72 中斷）| ❌ 作廢 | Kaggle 手動 Cancel → Kernel crash → Cell 7 未執行 → **best_v6 從未產生** |

依據：AI-course `docs/progress/2026-05-30-v6-training-interrupted.md`。

## ⚠️ 重要事實

- **目前不存在 best_v6 權重**（v6 訓練中斷）。
- 舊專案實際可用模型是 **v5（mAP 0.755）**。
- 但 v6/v5 皆為**舊專案** AI-course 的產物；本專案 (AIfinal) 從零重建程式碼，
  模型則沿用同一份 Kaggle 訓練 notebook。

## 當前狀態（2026-06-11）

- **正在 Kaggle 重跑訓練**（使用者執行中，結果尚未產出）。
- 重跑教訓：依舊紀錄，**訓練中途請勿 Cancel**，跑完 80 epochs 後直接在同一
  session 執行 Cell 7 匯出 ONNX，避免 Kernel crash。

## 待辦與 fallback

- [ ] Kaggle 訓練完成 → 取得 `best.pt` 的 mAP@50
- [ ] 填入 `accuracy_baseline.json`（目前為 null）
- [ ] 若新訓練 mAP ≥ 0.755 → 採用為 production；ADR-001 維持 v6 命名
- [ ] **Fallback**：若新訓練再次失敗或 < 0.755 → 改用 v5（需自 AI-course 取得
      v5 權重與其訓練設定，並更新 ADR-001 / CONTEXT / baseline 為 v5）

## 對 ADR-001 的影響

ADR-001（Accepted）目前以 `waste_sorter_v6` 命名。**暫不修改**，等本次 Kaggle
訓練結果出爐再決定：成功則維持，失敗則依上述 fallback 走 v5 並更新 ADR。
