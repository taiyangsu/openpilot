#!/usr/bin/env bash

# 确保该脚本可执行
chmod +x "$0"

# Mazda CSLC功能初始化 - 确保在任何其他操作之前执行
echo "初始化Mazda CSLC功能参数..."

# 创建参数目录（如果不存在）
mkdir -p /data/params/d

# 只创建CSLCEnabled参数，确保数值为1 (二进制01)
echo -n -e "\x01" > /data/params/d/CSLCEnabled
echo "CSLCEnabled参数已设置为1"

# 调试信息，查看文件内容的十六进制表示
if [ -f "/data/params/d/CSLCEnabled" ]; then
  echo "文件存在，内容如下："
  hexdump -C /data/params/d/CSLCEnabled
else
  echo "文件创建失败！"
fi

echo "Mazda CSLC功能初始化完成"

export API_HOST=https://api.konik.ai
export ATHENA_HOST=wss://athena.konik.ai

exec ./launch_chffrplus.sh
