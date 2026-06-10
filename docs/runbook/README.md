# Yahboom 實機操作指令 (Device Runbook)

> Claude 在 PC 寫程式碼；**以下步驟需由使用者在 Yahboom 實機上執行**。
> 隨各模組完成，本目錄會累積對應的實機指令與驗證步驟。

## 為什麼需要實機

這些工作 PC 上做不到，只能在 Yahboom（arm64 + GPU + GPIO + 攝影機）上做：
- TensorRT FP16 engine 編譯（`.engine` 裝置綁定）
- GPIO LED 實體點燈驗證（BOARD 模式）
- CSI IMX219 攝影機擷取
- `tegrastats` 抓 CPU%/GPU%/power
- `docker run --runtime nvidia` 實跑
- Self-hosted GitHub Actions runner 註冊
- Demo 影片錄製

## 指令清單（隨進度補充）

### 1. TensorRT engine 編譯（ADR-001）
```bash
# Kaggle 匯出 best_v6.onnx 後，在 Yahboom 上：
/usr/src/tensorrt/bin/trtexec --onnx=models/best_v6.onnx \
  --saveEngine=models/best_v6.engine --fp16
```

### 2. GPIO LED 點燈測試（ADR-002 / SPEC-002）
```bash
pip install Jetson.GPIO
# 逐腳測試（11=寶特瓶綠, 13=鐵鋁罐黃, 15=紙餐盒藍, 21=塑膠袋白, 23=一般垃圾紅）
python3 -c "import Jetson.GPIO as GPIO,time; GPIO.setmode(GPIO.BOARD); \
GPIO.setup(11,GPIO.OUT); GPIO.output(11,GPIO.HIGH); time.sleep(2); GPIO.cleanup()"
```

### 3. CSI 攝影機測試（SPEC-001）
```bash
# 確認 IMX219 被偵測
ls /dev/video0
# GStreamer 預覽
gst-launch-1.0 nvarguscamerasrc ! nvvidconv ! xvimagesink
```

### 4. Self-hosted runner 註冊（ADR-003）
> 待 CI build job 完成後補上（參考 HW6 Step 0.0 Option C）

### 5. tegrastats 抓數據（報告 §6 / B.8）
```bash
sudo tegrastats --interval 1000 --logfile tegrastats.log
# 另一終端跑推論 ≥60s，再用 scripts/parse_tegrastats.py 轉 utilization.csv
```

### 6. Docker 實跑（B.3）
> 待 Dockerfile 完成後補上 `docker pull` / `docker run --runtime nvidia`

---

> 每完成一個需要實機的模組，會在此補上「如何在 Yahboom 上驗證」的步驟。
