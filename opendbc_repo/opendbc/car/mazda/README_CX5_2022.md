# Mazda CX5 2022 优化版实验模式、CSLC功能和雷达支持

本文档介绍了为 Mazda CX5 2022 特别优化的 openpilot 实验模式、CSLC (Cruise Speed Limit Control) 功能和雷达支持。

## 特点和优化

我们对 Mazda CX5 2022 进行了一系列专门优化，使其成为 openpilot 支持的最佳马自达车型：

### 1. 转向控制优化

- **降低转向延迟**：`steerActuatorDelay` 从 0.1 降至 0.075，提供更快的转向响应
- **平滑转向释放**：`steerLimitTimer` 从 0.8 增至 0.85，减少转向释放时的突然感
- **优化转向比**：调整为 15.3，提供更精确的转向控制
- **增强转向响应速度**：提高 `STEER_DELTA_UP`，使转向更敏捷

### 2. 纵向控制优化

- **平滑加速控制**：使用优化的 PI 控制器参数，提供更自然的加速体验
- **改进停车体验**：调整 `stoppingDecelRate` 为 4.0，实现更舒适的停车过程
- **优化启动性能**：增加 `stopAccel` 和 `vEgoStarting` 参数，提供更流畅的起步

### 3. CSLC 功能增强

- **更低的最小速度设置**：CX5 2022 可以设置 25 km/h 的最小巡航速度
- **速度滤波器**：实现动态调整的速度滤波器，提供平滑的速度变化
- **智能按钮控制**：根据 CX5 2022 的特性优化按钮发送频率和阈值
- **自动恢复巡航**：优化停车后恢复巡航的逻辑，提高 Stop & Go 性能

### 4. 雷达支持（新增）

- **雷达数据处理**：添加对 CX5 2022 雷达数据的解析和处理
- **前车跟踪增强**：利用雷达数据提供更精确的前车距离和相对速度
- **改进跟车体验**：结合雷达和视觉数据，提供更平稳的跟车体验
- **自适应加速控制**：根据雷达检测到的前车状态调整加速度

## 使用方法

### 开启实验模式

1. 在 openpilot 界面进入设置
2. 切换到开发者页面
3. 开启"实验模式"
4. 重启 openpilot

### CSLC 功能使用

CSLC (Cruise Speed Limit Control) 会在实验模式开启时自动启用，它能够：

1. 通过模拟按下巡航控制按钮来精确控制车速
2. 自动调整到设定的目标速度
3. 提供更精确的跟车和自适应巡航功能

### 雷达功能使用

雷达功能会在 CX5 2022 车型上自动启用，无需额外设置：

1. 系统会自动检测并使用雷达数据
2. 界面上会显示雷达检测到的前车
3. 跟车距离控制会更加精确和平稳

### 特别提示

- CX5 2022 在实验模式下已经过优化，适合日常使用
- 系统会自动处理停车和启动情况，无需额外操作
- 在低速和停止情况下，系统能够自动发送 RESUME 信号继续行驶
- 雷达功能需要车辆硬件支持，请确保雷达系统正常工作

## 技术细节

1. **实验模式与 CSLC 集成**
   - 实验模式开启会自动启用 CSLC
   - CSLC 可以单独使用，不依赖实验模式

2. **车辆特定参数**
   ```python
   # CX5 2022 特有参数
   ret.longitudinalTuning.kpBP = [0., 5., 15., 30.]
   ret.longitudinalTuning.kpV = [1.3, 1.1, 0.9, 0.8]
   ret.longitudinalTuning.kiBP = [0., 5., 12., 20., 30.]
   ret.longitudinalTuning.kiV = [0.4, 0.3, 0.25, 0.2, 0.15]
   ```

3. **性能调整**
   - 按钮发送频率：每隔 8 帧发送一次（比普通马自达更快）
   - 速度调整阈值：6 km/h（考虑 CX5 2022 的特性）
   - 雷达更新频率：30Hz（提供更实时的前车信息）

4. **雷达数据处理**
   ```python
   # 雷达数据处理示例
   if lead_status and lead_distance > 0:
     desired_distance = max(10.0, CS.vEgo * 1.8)  # 1.8秒时间间隔
     distance_error = lead_distance - desired_distance
     accel_cmd = distance_error * 0.05 + lead_rel_speed * 0.2
   ```

## 常见问题

1. **实验模式无法开启？**
   - 确保 `CSLCEnabled` 参数已设置，可通过 SSH 执行 `echo -n "1" > /data/params/d/CSLCEnabled`

2. **车速控制不精确？**
   - CX5 2022 的速度控制是通过模拟按键实现的，有一定的延迟
   - 系统已经过优化，但仍有可能出现轻微波动

3. **停车后无法自动启动？**
   - 确保开启了实验模式
   - 系统会自动发送 RESUME 命令，但可能需要轻踩油门辅助

4. **雷达功能不工作？**
   - 确保车辆雷达硬件正常工作
   - 检查是否启用了 `CX5_2022` 标志
   - 可以通过查看日志文件 `/data/mazda_cx5_2022_config.log` 确认配置

## 后续开发计划

我们将继续优化 CX5 2022 的体验，计划包括：

1. 进一步改进低速控制精度
2. 增强停车和启动的平顺性
3. 优化与前车的跟车逻辑
4. 改进雷达和视觉融合算法

感谢您使用我们为 Mazda CX5 2022 特别优化的实验模式、CSLC 功能和雷达支持。如有问题或建议，请通过社区渠道反馈。

---

# Mazda CX5 2022 Optimized Experimental Mode, CSLC Function and Radar Support

This document introduces the specially optimized openpilot experimental mode, CSLC (Cruise Speed Limit Control) function, and radar support for Mazda CX5 2022.

## Features and Optimizations

We have made a series of specialized optimizations for the Mazda CX5 2022, making it the best Mazda model supported by openpilot:

### 1. Steering Control Optimization

- **Reduced steering delay**: `steerActuatorDelay` reduced from 0.1 to 0.075, providing faster steering response
- **Smooth steering release**: `steerLimitTimer` increased from 0.8 to 0.85, reducing sudden feeling when releasing steering
- **Optimized steering ratio**: Adjusted to 15.3, providing more precise steering control
- **Enhanced steering response speed**: Increased `STEER_DELTA_UP`, making steering more agile

### 2. Longitudinal Control Optimization

- **Smooth acceleration control**: Using optimized PI controller parameters for a more natural acceleration experience
- **Improved stopping experience**: Adjusted `stoppingDecelRate` to 4.0 for more comfortable stopping
- **Optimized starting performance**: Increased `stopAccel` and `vEgoStarting` parameters for smoother starts

### 3. CSLC Function Enhancement

- **Lower minimum speed setting**: CX5 2022 can set a minimum cruise speed of 25 km/h
- **Speed filter**: Implemented dynamically adjusting speed filter for smooth speed changes
- **Smart button control**: Optimized button sending frequency and thresholds based on CX5 2022 characteristics
- **Automatic cruise resumption**: Optimized logic for resuming cruise after stopping, improving Stop & Go performance

### 4. Radar Support (New)

- **Radar data processing**: Added parsing and processing of radar data for CX5 2022
- **Lead vehicle tracking enhancement**: Using radar data for more accurate lead vehicle distance and relative speed
- **Improved following experience**: Combining radar and vision data for smoother following experience
- **Adaptive acceleration control**: Adjusting acceleration based on radar-detected lead vehicle status

## Usage

### Enabling Experimental Mode

1. Go to settings in the openpilot interface
2. Switch to the developer page
3. Enable "Experimental Mode"
4. Restart openpilot

### Using CSLC Function

CSLC (Cruise Speed Limit Control) is automatically enabled when experimental mode is turned on, and it can:

1. Precisely control vehicle speed by simulating cruise control button presses
2. Automatically adjust to the set target speed
3. Provide more precise following and adaptive cruise functions

### Using Radar Function

Radar function is automatically enabled on CX5 2022 models without additional settings:

1. The system automatically detects and uses radar data
2. The interface displays lead vehicles detected by radar
3. Following distance control is more precise and smooth

### Special Notes

- CX5 2022 has been optimized for experimental mode and is suitable for daily use
- The system automatically handles stopping and starting situations without additional operations
- In low-speed and stopped situations, the system can automatically send RESUME signals to continue driving
- Radar function requires vehicle hardware support, please ensure the radar system is working properly

## Technical Details

1. **Experimental Mode and CSLC Integration**
   - Enabling experimental mode automatically enables CSLC
   - CSLC can be used independently, not dependent on experimental mode

2. **Vehicle-Specific Parameters**
   ```python
   # CX5 2022 specific parameters
   ret.longitudinalTuning.kpBP = [0., 5., 15., 30.]
   ret.longitudinalTuning.kpV = [1.3, 1.1, 0.9, 0.8]
   ret.longitudinalTuning.kiBP = [0., 5., 12., 20., 30.]
   ret.longitudinalTuning.kiV = [0.4, 0.3, 0.25, 0.2, 0.15]
   ```

3. **Performance Adjustments**
   - Button sending frequency: Every 8 frames (faster than regular Mazda)
   - Speed adjustment threshold: 6 km/h (considering CX5 2022 characteristics)
   - Radar update frequency: 30Hz (providing more real-time lead vehicle information)

4. **Radar Data Processing**
   ```python
   # Radar data processing example
   if lead_status and lead_distance > 0:
     desired_distance = max(10.0, CS.vEgo * 1.8)  # 1.8 second time gap
     distance_error = lead_distance - desired_distance
     accel_cmd = distance_error * 0.05 + lead_rel_speed * 0.2
   ```

## Common Issues

1. **Cannot enable experimental mode?**
   - Ensure the `CSLCEnabled` parameter is set, you can execute `echo -n "1" > /data/params/d/CSLCEnabled` via SSH

2. **Speed control not precise?**
   - CX5 2022 speed control is implemented by simulating button presses, there is some delay
   - The system has been optimized, but slight fluctuations may still occur

3. **Cannot automatically start after stopping?**
   - Make sure experimental mode is enabled
   - The system will automatically send RESUME commands, but may require light throttle assistance

4. **Radar function not working?**
   - Ensure vehicle radar hardware is working properly
   - Check if the `CX5_2022` flag is enabled
   - You can check the configuration by viewing the log file `/data/mazda_cx5_2022_config.log`

## Future Development Plans

We will continue to optimize the CX5 2022 experience, plans include:

1. Further improving low-speed control precision
2. Enhancing stopping and starting smoothness
3. Optimizing lead vehicle following logic
4. Improving radar and vision fusion algorithms

Thank you for using our specially optimized experimental mode, CSLC function, and radar support for Mazda CX5 2022. If you have any questions or suggestions, please provide feedback through community channels.