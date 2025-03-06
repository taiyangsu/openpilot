## 5. 常见问题排查

如果在测试过程中遇到问题，请检查以下几点：

1. **CSLC功能未启用**：
   - 确认车型是否为Mazda
   - 确认开关是否已正确启用
   - 检查日志中是否有相关错误信息
   - 如果出现`UnknownKeyName: b'CSLCEnabled'`错误，请运行初始化脚本：
     ```
     cd /data/openpilot/opendbc_repo/opendbc/car/mazda
     python3 init_params.py
     ```

2. **速度调整不正常**：
   - 确认原厂巡航控制系统是否正常工作
   - 检查巡航按钮模拟是否正确
   - 验证速度单位设置（公制/英制）是否正确
   - 确认最大巡航速度常量（V_CRUISE_MAX）设置是否合理，默认为160 km/h

3. **功能间歇性失效**：
   - 检查CAN总线连接是否稳定
   - 检查设备温度是否过高
   - 检查是否有其他功能干扰

4. **导入错误**：
   - 如果遇到导入错误，特别是关于`V_CRUISE_MAX`的错误，请确认`carcontroller.py`文件中已经本地定义了这个常量，而不是从`drive_helpers.py`导入

## 6. 系统初始化

为确保CSLC功能正常工作，系统需要正确初始化以下参数：

1. **CSLCEnabled**: 控制CSLC功能的开关，默认为`true`
2. **CSLCSpeed**: CSLC目标速度，单位为m/s，默认为0.0

系统提供了自动初始化脚本，位于：
```
/data/openpilot/opendbc_repo/opendbc/car/mazda/init_params.py
```

如果系统启动后出现参数未定义的错误，可以手动运行此脚本：
```
cd /data/openpilot/opendbc_repo/opendbc/car/mazda
python3 init_params.py
```

也可以将启动脚本添加到系统启动项中：
```
cd /data/openpilot/opendbc_repo/opendbc/car/mazda
chmod +x launch_init.sh
./launch_init.sh
```