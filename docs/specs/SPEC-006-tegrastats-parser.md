# SPEC-006 — Tegrastats 解析器 (TegrastatsParser)

| 欄位 | 內容 |
|------|------|
| **Status** | Draft |
| **Date** | 2026-06-11 |
| **ADR 依據** | ADR-003（CI/CD：integration-test 階段產出效能 artifacts）|
| **對應源碼** | `src/tegrastats_parser.py`、`scripts/parse_tegrastats.py`（CLI shim）|

---

## 功能描述 (What)

`TegrastatsParser` 把 Yahboom 實機 `tegrastats` 輸出（`tegrastats.log`）解析成
結構化資料列，並轉成 `utilization.csv`，供報告 §6（系統效能結果）與 B.8
test artifacts 使用。純文字解析、無硬體相依，可在 PC 上完整單元測試。

> 實機資料由使用者在 Yahboom 上以 `sudo tegrastats --interval 1000 --logfile tegrastats.log`
> 抓取（runbook §5）；本解析器在 PC/CI 上把 log 轉成 CSV 與摘要。

---

## tegrastats 行格式（相容 JetPack 5/6）

兩種電源欄位命名都要支援：
- 舊（POM）：`POM_5V_IN 3456/3400`
- Orin（VDD）：`VDD_IN 4924/4924`

範例行：
```
RAM 4190/7765MB (lfb 18x4MB) SWAP 0/3882MB CPU [10%@1479,20%@1479,off,30%@1479] EMC_FREQ 0% GR3D_FREQ 45% ... VDD_IN 4924/4924 VDD_SOC 1314/1314
```
可選前綴時間戳（`--timestamp`）：`06-11-2026 14:00:01 RAM ...`

擷取欄位：
| 欄位 | 來源 | 規則 |
|------|------|------|
| `timestamp` | 行首 `MM-DD-YYYY HH:MM:SS` | 無則為 `None` |
| `cpu_pct` | `CPU [...]` | 各核 `N%` 平均；`off` 核略過 |
| `gpu_pct` | `GR3D_FREQ N%` | 整數 |
| `power_mw` | `POM_5V_IN`/`VDD_IN` 的 `瞬時/平均` 取瞬時值 | 整數 mW |
| `ram_used_mb` / `ram_total_mb` | `RAM used/totalMB` | 整數 |

---

## 介面設計

```python
class TegrastatsParser:
    def parse_line(self, line: str) -> dict | None: ...   # 無效行 → None
    def parse_text(self, text: str) -> list[dict]: ...
    def to_csv(self, rows: list[dict]) -> str: ...        # 含表頭
    def summary(self, rows: list[dict]) -> dict: ...      # avg/max cpu/gpu/power
```

CSV 表頭：`index,timestamp,cpu_pct,gpu_pct,power_mw,ram_used_mb,ram_total_mb`

`summary()` 回傳：`{samples, cpu_avg, cpu_max, gpu_avg, gpu_max, power_avg_mw, power_max_mw}`

---

## 七欄位 SPEC

| 欄位 | 內容 |
|------|------|
| **Feature** | tegrastats log → 結構化 CSV + 效能摘要（報告 §6 / B.8 artifacts）|
| **User Story** | 使用者在 Yahboom 抓 ≥60s tegrastats.log，於 PC/CI 跑 `parse_tegrastats.py` 得 utilization.csv 與 CPU/GPU/power 摘要 |
| **Inputs** | tegrastats 文字（多行）；POM 或 VDD 電源命名皆可；可含/不含時間戳 |
| **Outputs** | `list[dict]` 結構化列；`utilization.csv` 字串；摘要 dict（avg/max）|
| **Rules** | CPU% = 各活躍核平均（`off` 略過）；GPU% = GR3D_FREQ；power = `*_IN` 瞬時 mW；CSV 含表頭與 index |
| **Edge Cases** | 空行/無 RAM 與 CPU 的雜訊行 → 略過（parse_line 回 None）；全 `off` 核 → cpu_pct=0.0；缺電源欄位 → power_mw=None；空輸入 → summary 各值 0 / samples=0 |
| **Done When** | 單元測試覆蓋：POM 與 VDD 兩格式、off 核、時間戳前綴、雜訊行略過、to_csv 表頭與列數、summary avg/max、空輸入；模組覆蓋率 ≥90% |

---

## 測試計畫（TDD）

| 測試 | 預期 |
|------|------|
| `test_parse_line_vdd_format` | VDD_IN 行 → cpu/gpu/power/ram 正確 |
| `test_parse_line_pom_format` | POM_5V_IN 行 → power 取瞬時值 |
| `test_parse_line_skips_off_cores` | `off` 核不計入 CPU 平均 |
| `test_parse_line_all_off_cores` | 全 off → cpu_pct=0.0 |
| `test_parse_line_with_timestamp` | 前綴時間戳被擷取 |
| `test_parse_line_noise_returns_none` | 空行/雜訊 → None |
| `test_parse_line_missing_power` | 無 *_IN → power_mw=None |
| `test_parse_text_filters_noise` | 多行含雜訊 → 只回有效列 |
| `test_to_csv_header_and_rows` | CSV 表頭 + 正確列數 + index 遞增 |
| `test_summary_avg_max` | avg/max 計算正確 |
| `test_summary_empty` | 空輸入 → samples=0、各值 0 |
