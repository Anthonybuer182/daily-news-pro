#!/usr/bin/env bash
# =============================================================================
# Daily News Pro — 服务器端一键部署脚本（Ubuntu，2G 内存优化）
#
# 用法（在服务器上执行）：
#   sudo bash deploy.sh            # 首次部署 / 更新
#   sudo APP_DIR=/opt/dnp bash deploy.sh   # 自定义安装路径
#
# 本脚本做这些事（均幂等，可重复执行）：
#   1. 创建 2G swap（防 pip 编译 lxml / Playwright 运行时 OOM）—— 首次
#   2. 创建 Python venv + 安装依赖（优先用预编译 wheel，避免编译吃内存）
#   3. 安装 Playwright Chromium + 系统依赖库 —— 仅首次
#   4. 安装 systemd service 并启动
#
# 前端 dist 不在此处构建（服务器跑 Vite 会 OOM）：
#   请在本地用 build-and-upload.ps1 构建并上传 dist 到 frontend/dist。
# =============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/daily-news-pro}"
VENV_DIR="${VENV_DIR:-$APP_DIR/venv}"
SERVICE_NAME="daily-news"
PYTHON="${PYTHON:-python3}"

echo ">>> APP_DIR = $APP_DIR"
cd "$APP_DIR"

# -----------------------------------------------------------------------------
# 1. Swap（防 OOM 的关键兜底）
# -----------------------------------------------------------------------------
if ! swapon --show | grep -q '/swapfile'; then
    echo ">>> 创建 2G swap ..."
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "    swap 已启用"
else
    echo ">>> swap 已存在，跳过"
fi

# -----------------------------------------------------------------------------
# 2. Python venv + 依赖
# -----------------------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo ">>> 创建 venv ..."
    $PYTHON -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo ">>> 安装 Python 依赖（优先预编译 wheel，避免编译 OOM）..."
pip install --upgrade pip --quiet
# --only-binary 优先用 wheel，lxml/playwright 等都有预编译包，避免现场编译
pip install --only-binary :all: -r "$APP_DIR/backend/requirements.txt" --quiet \
    || pip install -r "$APP_DIR/backend/requirements.txt" --quiet

# -----------------------------------------------------------------------------
# 3. Playwright Chromium（保留必装）+ 系统依赖库
# -----------------------------------------------------------------------------
if [ ! -d "$HOME/.cache/ms-playwright" ] || [ -z "$(ls -A "$HOME/.cache/ms-playwright" 2>/dev/null)" ]; then
    echo ">>> 安装 Playwright Chromium 及系统依赖（首次较慢）..."
    playwright install chromium
    playwright install-deps chromium 2>/dev/null || echo "    install-deps 需 sudo，若已用 sudo 运行则已生效"
else
    echo ">>> Playwright Chromium 已存在，跳过"
fi

# -----------------------------------------------------------------------------
# 4. systemd service
# -----------------------------------------------------------------------------
# 把脚本同目录的 service 文件拷到 systemd（按实际路径覆盖变量）
SERVICE_SRC="$APP_DIR/daily-news.service"
if [ -f "$SERVICE_SRC" ]; then
    # 用实际安装路径生成最终 unit 文件
    TMP_UNIT="$(mktemp)"
    sed -e "s#/opt/daily-news-pro#$APP_DIR#g" \
        -e "s#/opt/daily-news-pro/venv#$VENV_DIR#g" \
        "$SERVICE_SRC" > "$TMP_UNIT"
    cp "$TMP_UNIT" "/etc/systemd/system/$SERVICE_NAME.service"
    rm -f "$TMP_UNIT"

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl restart "$SERVICE_NAME"
    echo ">>> 已安装并重启 systemd 服务: $SERVICE_NAME"
else
    echo "!!! 未找到 $SERVICE_SRC，请确保该文件在仓库中"
fi

# -----------------------------------------------------------------------------
# 5. 检查 .env
# -----------------------------------------------------------------------------
if [ ! -f "$APP_DIR/backend/.env" ]; then
    echo ">>> 复制 .env.example -> .env（请务必修改 ADMIN_PASSWORD / SECRET_KEY / STATIC_DIR）"
    cp "$APP_DIR/backend/.env.example" "$APP_DIR/backend/.env"
fi

echo ""
echo "==================== 部署完成 ===================="
echo " 服务状态 : systemctl status $SERVICE_NAME"
echo " 日志     : journalctl -u $SERVICE_NAME -f"
echo " 访问     : http://<服务器IP>:8000"
echo ""
echo " 提醒："
echo "  1. 编辑 backend/.env：设置 ADMIN_PASSWORD、SECRET_KEY、STATIC_DIR"
echo "  2. STATIC_DIR 建议设为 $APP_DIR/frontend/dist"
echo "  3. 前端 dist 需在本地构建后上传（见 build-and-upload.ps1）"
echo "================================================="
