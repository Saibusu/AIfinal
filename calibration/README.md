# calibration/ — INT8 校正（選用）

目前部署精度為 **TensorRT FP16**（見 ADR-001），尚未使用 INT8。

若未來改用 INT8 量化，此目錄存放：
- 校正資料集（calibration dataset）
- 校正腳本（`calibrate.py`）

FP16 已滿足 ≥ 15 FPS 目標，INT8 為選用優化方向。
