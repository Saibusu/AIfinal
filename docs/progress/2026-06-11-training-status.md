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

## 模型版本決策（2026-06-11 鎖定）

> **決策：一律採用 v6，不採用 v5。**
> 理由：v5 訓練本身也不完全（非完整、可信的 production 基準），因此即使 v6 的
> mAP 低於 v5 的 0.755，仍以 v6 為準。**v5 不作為 fallback。**

- v6 = 本專案唯一的 production 模型路線（YOLO26m，5 類，本 notebook 重跑）
- ADR-001 的 `waste_sorter_v6` 命名**確定維持**，不再有版本變更分支

## ✅ 訓練完成結果（2026-06-11，Kaggle T4）

- 76 epochs（patience=20 提早收斂，非中斷）；11.6 小時
- **整體 mAP@50 = 0.731**（> ADR-001 目標 0.65 ✅）；mAP@50-95 = 0.508
- 推論 11.9ms/張（T4，640）
- 各類別 mAP50：鐵鋁罐 0.882｜紙餐盒 0.781｜一般垃圾 0.754｜寶特瓶 0.681｜**塑膠袋 0.52（弱，recall 0.436）**
- 數據已填入 `accuracy_baseline.json`（來源：validation split 1092 張）

> 存檔路徑 `runs/detect/runs/train/waste_sorter_v6`（ultralytics 自動加 runs/detect）—
> 即先前 FileNotFoundError 主因，已用 `model.trainer.best` 修正。

## 待辦

- [ ] 補跑 test split（546 張）的 mAP → 更新 baseline 為 test 數據
- [ ] 下載 best_v6.pt / best_v6.onnx
- [ ] 在 Yahboom 上轉 TensorRT FP16 engine 並實測 FPS / mAP（on-device 數據才是報告 §6 最終值）
- [ ] 塑膠袋弱點 → 寫入報告 §6/§7（防呆機制接住：低信心→一般垃圾）

> 無論 mAP 數值為何，模型版本決策已定（v6），不因數值回頭改用 v5。
