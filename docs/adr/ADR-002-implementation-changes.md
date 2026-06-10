# ADR-002 — 實作變動：鋁箔包分類、蜂鳴器、Yahboom GPIO

| 欄位 | 內容 |
|------|------|
| **Status** | Draft |
| **Date** | 2026-06-11 |
| **Authors** | 李軒杰 (I4A70), 黃義鈞 (I4B58) |
| **Supersedes** | 期中提案書第 1.3 節（類別定義）、第 4.1 節（ACT 行動） |

---

## 背景 (Context)

期中提案（Week 9）定義了 6 類垃圾分類，並包含蜂鳴器致動器。
實作期間有三處變動需要正式記錄，以符合課程 FAQ：
「Final scope differs from proposal → document the change in §2 of the report.」

---

## 變動一：鋁箔包 → 歸入一般垃圾

### 提案原設計
| ID | 類別 | LED |
|----|------|-----|
| 5  | 鋁箔包 (Tetra Pak) | 白 |

### 變動後設計
鋁箔包（Tetra Pak）歸入 **class 4 一般垃圾**。總類別數：6 → **5**。

### 決策理由
1. **資料不平衡**：Roboflow 資料集中 Tetra Pack（原始 class 36）樣本極少
2. **分類歧義**：鋁箔包為複合材質（紙+鋁+塑膠），台灣各縣市分類規則不一，部分地區確實歸一般垃圾
3. **模型效能**：移除樣本過少的類別可提高整體 mAP@50
4. **Notebook 已對齊**：`waste_sorter_v6` 的 5 類別設定已按此實作

---

## 變動二：取消蜂鳴器

### 提案原設計
蜂鳴器透過 GPIO 數位輸出，辨識成功時與 LED 同步發出提示音。

### 變動後設計
移除蜂鳴器，僅保留 LED 視覺指示。

### 決策理由
1. **Yahboom 套裝限制**：Yahboom 套件的 GPIO 腳位已被 LED 佔用，增加蜂鳴器需要額外電路
2. **Demo 環境考量**：課堂展示環境嘈雜，蜂鳴器效果有限
3. **課程規範滿足**：課程要求「驅動至少一個物理致動器」，LED 已滿足此要求

---

## 變動三：Yahboom 套裝 GPIO 針腳差異

### 提案原設計
假設使用標準 Jetson Orin Nano DevKit GPIO 針腳。

### 變動後設計
使用 **Yahboom 套裝指定針腳**（BOARD 編號模式）：

| class ID | 類別 | GPIO Pin | LED 顏色 |
|---------|------|----------|---------|
| 0 | 寶特瓶 | **Pin 11** | 綠 |
| 1 | 鐵鋁罐 | **Pin 13** | 黃 |
| 2 | 紙餐盒 | **Pin 15** | 藍 |
| 3 | 塑膠袋 | **Pin 21** | 白 |
| 4 | 一般垃圾 | **Pin 23** | 紅 |

### 決策理由
1. Yahboom 套裝的排列與 NVIDIA DevKit 不同，需依 Yahboom 硬體文件確認
2. 使用 BOARD 模式（物理針腳）而非 BCM 模式，確保與 Yahboom 文件一致
3. GPIO 針腳統一在 `src/actuator_controller.py` 管理，方便未來調整

### 注意事項
- **待確認**：Yahboom 針腳對應需在實際硬體上驗證，如有差異應更新此 ADR
- 測試環境使用 Mock GPIO，不依賴實際硬體

---

## 後果 (Consequences)

**正面：**
- 5 類別資料集更平衡，訓練效果更好
- 系統硬體更簡潔，減少接線複雜度
- GPIO 設定集中管理，易於針對 Yahboom 調整

**負面：**
- 鋁箔包使用者無法獲得精確指引（但仍可投入一般垃圾桶）
- 報告需說明與提案的差異（§2 架構說明）

---

## 驗收條件 (Done When)

- [ ] `src/actuator_controller.py` 中 GPIO 針腳以常數定義（可透過 env var 覆蓋）
- [ ] 測試中 GPIO 以 Mock 替代，CI 可通過
- [ ] `report/FINAL_REPORT.pdf` §2 說明三項變動及理由
- [ ] Yahboom 針腳在實機上驗證點亮正確 LED

---

> **注意**：Status 為 Draft，未經人類核准前不得有對應生產代碼。
