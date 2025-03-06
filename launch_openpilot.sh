#!/usr/bin/env bash

# 初始化Mazda CSLC功能参数 - 在任何其他操作之前执行
if [ -d "/data/params/d" ]; then
  # 确保CSLCEnabled参数默认开启
  if [ ! -f "/data/params/d/CSLCEnabled" ]; then
    echo "初始化CSLCEnabled参数..."
    echo "1" > /data/params/d/CSLCEnabled
  fi

  # 确保MazdaCSLC参数默认开启
  if [ ! -f "/data/params/d/MazdaCSLC" ]; then
    echo "初始化MazdaCSLC参数..."
    echo "1" > /data/params/d/MazdaCSLC
  fi

  echo "Mazda CSLC功能初始化完成"
fi

export API_HOST=https://api.konik.ai
export ATHENA_HOST=wss://athena.konik.ai

exec ./launch_chffrplus.sh
