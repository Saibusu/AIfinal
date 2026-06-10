# data/ — 資料

| 路徑 | 用途 |
|------|------|
| `held-out/` | 評估用 held-out test set（546 張，僅小型影像）|

## 資料集來源（見 ADR-002 變動四）

- 來源：Roboflow `projectverba/yolo-waste-detection` v1
- 原始 42 類 → 映射為本專案 5 類（映射邏輯見 [../notebooks/train_waste_sorter_v6.ipynb](../notebooks/train_waste_sorter_v6.ipynb) Cell 5）
- 切分：train 11,466 / valid 1,092 / test 546

**大型資料**（完整訓練集、模型權重）不進 git，
放入 `<team>_test_artifacts.zip`（TronClass 上傳）或 Git LFS。

held-out test set 用於 `accuracy_baseline.json` 的 accuracy gate 評估。
