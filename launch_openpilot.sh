#!/usr/bin/env bash

# Mazda CSLC功能初始化 - 确保在任何其他操作之前执行
echo "初始化Mazda CSLC功能参数..."

# 创建参数目录（如果不存在）
mkdir -p /data/params/d

# 使用直接的方法创建参数文件
echo -n "1" > /data/params/d/CSLCEnabled
echo -n "1" > /data/params/d/MazdaCSLC

echo "Mazda CSLC功能初始化完成"

export API_HOST=https://api.konik.ai
export ATHENA_HOST=wss://athena.konik.ai

exec ./launch_chffrplus.sh
