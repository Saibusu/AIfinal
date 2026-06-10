# deploy/ — 部署設定

對應 ADR-003（CI/CD Pipeline）。計畫檔案：

| 檔案 | 用途 |
|------|------|
| `docker-compose.yml` | 定義 runtime、network、volume mounts（一鍵 demo）|
| `deploy.sh` | tag-triggered 部署腳本（在 Jetson 上執行）|
| `healthcheck.sh` | 容器健康檢查 |
| `rollback.sh` | 回滾至前一個 tag（目標 < 30 秒）|

所有 `.sh` 需 `#!/usr/bin/env bash` shebang + Copyright header。
