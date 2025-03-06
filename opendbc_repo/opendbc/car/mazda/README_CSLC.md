# Mazda CSLC功能使用指南

## 功能介绍

CSLC (Cruise Speed Limit Control) 是一个为Mazda车型设计的自动控制车速功能。它通过模拟按下巡航控制按钮来调整车速，使车辆能够自动保持在设定的速度限制内。

## 参数说明

CSLC功能使用以下参数来控制其行为：

1. **CSLCEnabled**: 控制CSLC功能的总开关
   - 位置: `/data/params/d/CSLCEnabled`
   - 默认值: `true`（开启）
   - 可通过开发者面板中的CSLC开关控制

2. **MazdaCSLC**: 控制CSLC功能是否在Mazda车型上启用
   - 位置: `/data/params/d/MazdaCSLC`
   - 默认值: `true`（开启）
   - 此参数确保CSLC功能只在Mazda车型上生效

3. **CSLCSpeed**: 设置CSLC功能的目标速度
   - 位置: `/data/params/d/CSLCSpeed`
   - 单位: m/s
   - 如果未设置，则使用HUD显示的巡航速度

4. **SpeedFromPCM**: 控制是否使用PCM提供的速度
   - 位置: `/data/params/d/SpeedFromPCM`
   - 默认值: `1`（使用PCM速度）

5. **IsMetric**: 控制速度单位是否为公制
   - 位置: `/data/params/d/IsMetric`
   - 默认值: 根据系统设置

6. **ExperimentalMode**: 控制是否使用实验模式
   - 位置: `/data/params/d/ExperimentalMode`
   - 默认值: `false`（关闭）
   - 实验模式下，CSLC会根据当前加速度动态调整目标速度

## 使用方法

1. **启用CSLC功能**:
   - 进入开发者面板
   - 打开CSLC开关
   - 系统会自动创建并启用所需的参数

2. **设置目标速度**:
   - 通过OpenPilot界面设置巡航速度
   - 或者通过SSH连接到设备，手动设置CSLCSpeed参数:
     ```bash
     echo "25.0" > /data/params/d/CSLCSpeed  # 设置目标速度为25 m/s (约90 km/h)
     ```

3. **实验模式**:
   - 如果需要更平滑的速度控制，可以启用实验模式:
     ```bash
     echo "1" > /data/params/d/ExperimentalMode
     ```

## 注意事项

1. CSLC功能只在Mazda车型上生效，即使在其他车型上启用了该功能
2. 使用CSLC功能时，请确保车辆处于安全环境中
3. CSLC功能通过模拟按下巡航控制按钮来调整车速，可能会与手动操作巡航控制按钮产生冲突
4. 如果遇到问题，可以尝试重启设备或重置参数:
   ```bash
   rm /data/params/d/CSLCEnabled
   rm /data/params/d/MazdaCSLC
   ```

## 故障排除

如果CSLC功能不工作，请检查以下几点：

1. 确认CSLCEnabled和MazdaCSLC参数都已设置为true
2. 确认车型为Mazda
3. 确认OpenPilot已启用并正常工作
4. 检查日志中是否有相关错误信息

## 开发者信息

CSLC功能的核心实现在以下文件中：

- `opendbc_repo/opendbc/car/mazda/mazdacan.py`: 实现了CAN消息的生成
- `opendbc_repo/opendbc/car/mazda/carcontroller.py`: 实现了CSLC功能的控制逻辑
- `selfdrive/ui/qt/offroad/developer_panel.cc`: 实现了CSLC开关的UI