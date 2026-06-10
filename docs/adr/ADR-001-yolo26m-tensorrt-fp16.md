# ADR-001 — 模型選擇：YOLO26m + TensorRT FP16

| 欄位 | 內容 |
|------|------|
| **Status** | Accepted |
| **Date** | 2026-06-11 |
| **Authors** | 李軒杰 (I4A70), 黃義鈞 (I4B58) |
| **Supersedes** | — |
| **Superseded by** | — |

---

## 背景 (Context)

本系統需在 Yahboom (Jetson Orin Nano 相容套件，8 GB RAM、最大 25W) 上
進行即時垃圾分類推論，目標 ≥ 15 FPS，端到端延遲 < 200ms。

期中提案選用 YOLO26（nano 版，3.2M 參數），Kaggle 訓練實際使用 YOLO26m（25.9M 參數）。

---

## 決策 (Decision)

**使用 YOLO26m + TensorRT FP16，輸入解析度 416×416。**

訓練設定：
- Epochs: 80, patience: 20
- Batch: 16, imgsz: 640（訓練），416（TensorRT 匯出）
- 增強：copy_paste=0.3, mosaic=1.0, cls=0.3

部署：
- 匯出 ONNX（opset 12，simplify=True）→ TensorRT FP16 engine
- engine 檔案不進版本控制（裝置綁定），需在目標裝置上重新編譯

---

## 理由 (Rationale)

| 比較項目 | YOLO26 (3.2M) | **YOLO26m (25.9M)** | YOLO26l (43.7M) |
|---------|--------------|---------------------|-----------------|
| 模型大小 | ~6 MB | ~52 MB | ~87 MB |
| 預期 mAP@50 | 基準 | +5–8 pts | +8–12 pts |
| Orin Nano RAM | ✅ 充裕 | ✅ 可行 | ⚠️ 緊張 |
| TensorRT FP16 後 FPS | ~30+ | ~20–25 | ~12–15 |

選 YOLO26m 的原因：
1. 5 類別資料集（含塑膠袋少數類別）需要更強的特徵提取能力
2. copy_paste 增強需要更大容量模型才能有效學習
3. TensorRT FP16 後仍可達到 ≥ 15 FPS 目標
4. 52MB 模型在 8GB RAM 下完全可行

---

## 後果 (Consequences)

**正面：**
- 更高的 mAP@50（預期 ≥ 0.65）
- 對少數類別（塑膠袋、寶特瓶）更佳的泛化能力

**負面：**
- TensorRT engine 編譯需要 10–20 分鐘（CI 中延遲推論引擎編譯至 entrypoint）
- Dockerfile build 不含 engine 編譯，初次啟動需等待

**緩解措施：**
- Dockerfile entrypoint 在啟動時自動編譯（若 `.engine` 不存在）
- 提供預編譯 engine 下載腳本（`scripts/download_engine.sh`）

---

## 驗收條件 (Done When)

- [ ] ONNX 匯出成功（`best_v6.onnx`）
- [ ] TensorRT FP16 engine 在 Yahboom 上編譯成功
- [ ] 推論 FPS ≥ 15（`tegrastats` 確認 GPU 使用率 > 60%）
- [ ] mAP@50 ≥ 0.65 於 held-out test set（546 張）
- [ ] `accuracy_baseline.json` 記錄基線數值

---

> **注意**：Status 已由人類核准為 **Accepted**（2026-06-11）。後續變更須新增 superseding ADR，不可直接改寫已核准的決策內容。
