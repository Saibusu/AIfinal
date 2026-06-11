# models/ — 模型權重

> 權重檔**不入版控**（device-bound + 體積大，見 `.gitignore`）。本目錄只保留本說明。
> 實機部署時把權重放這裡；`deploy/docker-compose.yml` 會 mount `../models → /app/models`。

## 檔案

| 檔案 | 大小 | 用途 | 是否入 git |
|------|------|------|-----------|
| `best_v6.pt` | 42 MB | PyTorch 權重（訓練產物、可再匯出）| ❌ gitignored |
| `best_v6.onnx` | 77.9 MB | ONNX（opset 12, imgsz 416）→ 供 TensorRT 編譯 | ❌ gitignored |
| `best_v6.engine` | — | TensorRT FP16 engine（**在 Yahboom 上編譯**，裝置綁定）| ❌ gitignored |

## 模型卡（waste_sorter_v6）

- 架構：YOLO26m（132 layers, 20.35M params, 67.9 GFLOPs）
- 訓練：Kaggle Tesla T4，76 epochs（patience=20，best @ epoch 56），11.13 小時
- 影像尺寸：**416**（ONNX input shape `(1,3,416,416)`，output `(1,300,6)`）
- 資料集：Roboflow `projectverba/yolo-waste-detection` v1（5 類）
- 驗證 split（1092 張）：**mAP@50 = 0.731**、mAP@50-95 = 0.508、P = 0.787、R = 0.691
- 速度（T4）：preprocess 0.2ms / inference 11.3ms / postprocess 0.2ms
- 各類別 mAP50：鐵鋁罐 0.882｜紙餐盒 0.781｜一般垃圾 0.79｜寶特瓶 0.681｜**塑膠袋 0.52（弱，R 0.436）**
- 完整數據見 `../accuracy_baseline.json`

## 如何取得權重

訓練 notebook：`../notebooks/train_waste_sorter_v6.ipynb`（Kaggle）。
跑完後從 Kaggle Output 下載 `best_v6.pt` + `best_v6.onnx`，放入本目錄。

## 在 Yahboom 上編譯 engine（ADR-001 / runbook §1）

容器 entrypoint 會在 `best_v6.engine` 不存在時自動編譯：
```bash
/usr/src/tensorrt/bin/trtexec --onnx=models/best_v6.onnx \
  --saveEngine=models/best_v6.engine --fp16
```

## 待辦（on-device）

- [ ] 在 Yahboom 編譯 `best_v6.engine` 並實測 FPS / mAP（報告 §6 最終值）
- [ ] 補 TEST split（546 張）mAP → 更新 baseline 的 metric_source
- [ ] 驗證 ONNX opset12 advanced-indexing 警告不影響偵測正確性（實機 sanity check）

> 若要把權重納入版控，改用 Git LFS（目前刻意不納，避免 repo 膨脹）。
