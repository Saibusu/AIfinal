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
CI build job 已完成（`.github/workflows/ci.yml` 的 `integration-test` job，labels
`[self-hosted, linux, ARM64, jetson]`）。在 Yahboom 上註冊 runner：
```bash
# GitHub repo → Settings → Actions → Runners → New self-hosted runner (Linux ARM64)
mkdir actions-runner && cd actions-runner
curl -o runner.tar.gz -L <下載連結>   # 依頁面指示
tar xzf runner.tar.gz
./config.sh --url https://github.com/Saibusu/AIfinal --token <TOKEN> \
  --labels jetson --name yahboom
./run.sh        # 顯示 Idle 後，push 到 master 會觸發 integration-test
```

### 5. tegrastats 抓數據（報告 §6 / B.8）
```bash
sudo tegrastats --interval 1000 --logfile tegrastats.log
# 另一終端跑推論 ≥60s，再用 scripts/parse_tegrastats.py 轉 utilization.csv
```

### 6. Docker 實跑（B.3）
Dockerfile + compose 已完成。在 Yahboom 上（先把 `best_v6.onnx`/`.engine` 放到 `models/`）：
```bash
# 方式 A：compose 一鍵（engine 不存在時 entrypoint 會自動 trtexec 編譯）
cd deploy && IMAGE_REF=ghcr.io/saibusu/aifinal:latest docker compose up -d
./healthcheck.sh                      # 等 /health 回 200
# 瀏覽器開 http://<jetson-ip>:8000 看即時畫面 + 偵測事件 + FPS

# 方式 B：直接 docker run
docker run --runtime nvidia --rm -p 8000:8000 \
  -v $PWD/models:/app/models \
  -v /tmp/argus_socket:/tmp/argus_socket \
  --device /dev/gpiochip0 \
  ghcr.io/saibusu/aifinal:latest
```
> 影像由 CI build job 推上 GHCR；首次需 `docker login ghcr.io`（若 package 設私有）。

---

> 每完成一個需要實機的模組，會在此補上「如何在 Yahboom 上驗證」的步驟。
