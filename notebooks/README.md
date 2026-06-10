# notebooks/ — 訓練 Notebook

| 檔案 | 用途 |
|------|------|
| `train_waste_sorter_v6.ipynb` | Kaggle 訓練 notebook（YOLO26m，80 epochs，Tesla T4）|

## 訓練流程摘要

1. Cell 1–3：GPU 確認、安裝套件、clone 專案
2. Cell 4：從 Roboflow 下載資料集（API Key 存於 Kaggle Secrets，**勿硬編碼**）
3. Cell 5：42 類 → 5 類映射（`NAME_MAP`）+ 重新標註
4. Cell 6：訓練 YOLO26m → `waste_sorter_v6`，輸出 `best_v6.pt`
5. Cell 7：匯出 ONNX（imgsz=416, opset=12）→ Jetson 上轉 TensorRT FP16

對應決策：ADR-001（模型）、ADR-002 變動四（資料集來源）。

> 注意：Roboflow API Key 一律從 Kaggle Secrets 讀取，切勿寫入 notebook 後上傳。
