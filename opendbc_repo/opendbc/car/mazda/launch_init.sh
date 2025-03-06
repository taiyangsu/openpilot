#!/bin/bash

# 设置脚本路径
SCRIPT_DIR="/data/openpilot/opendbc_repo/opendbc/car/mazda"
INIT_SCRIPT="$SCRIPT_DIR/init_params.py"

# 确保脚本可执行
chmod +x "$INIT_SCRIPT"

# 在后台运行初始化脚本
python3 "$INIT_SCRIPT" &

echo "Mazda参数初始化脚本已启动"