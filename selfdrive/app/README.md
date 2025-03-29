# CommaAssist - Comma3数据广播与监控工具

这个文件夹包含用于获取Comma3数据并在局域网中广播的实用工具，以及接收和显示这些数据的客户端工具。

## 工具列表

1. **commassit.py** - 运行在Comma3设备上的数据广播服务
2. **commalisten.py** - 终端界面的数据监控工具
3. **commawebview.py** - 基于Web的数据监控界面

## 安装依赖

对于服务端(Comma3设备)，所有依赖已预先安装。

对于客户端(接收端)，需要安装以下依赖：

```bash
# 终端界面所需依赖
pip install curses

# Web界面所需依赖
pip install flask
```

## 使用方法

### 服务端 (Comma3设备)

在Comma3设备上启动服务：

```bash
cd /data/openpilot
python selfdrive/app/commassit.py
```

这将启动广播服务，默认在端口8088上广播数据。

### 客户端 (接收端)

#### 终端界面监控

```bash
# 默认端口8088
python selfdrive/app/commalisten.py

# 指定端口
python selfdrive/app/commalisten.py -p 8088
```

#### Web界面监控

```bash
# 默认配置 (UDP端口8088, Web端口5000)
python selfdrive/app/commawebview.py

# 自定义配置
python selfdrive/app/commawebview.py -p 8088 -w 5000 --host 0.0.0.0
```

然后在浏览器中访问 `http://<你的IP>:5000` 查看Web监控界面。

**注意**：如果要使用地图功能，需要在commawebview.py中替换Google Maps API密钥。

## 广播的数据内容

广播数据以JSON格式发送，主要包含以下信息：

- **设备信息**：IP地址、电池状态、系统资源使用情况
- **车辆信息**：速度、方向盘角度、档位、制动和油门状态等
- **GPS位置**：经纬度、方向、海拔和精度信息
- **导航信息**：目的地距离、预计到达时间、限速和下一个导航动作

## 自定义和扩展

您可以根据需要修改这些脚本，添加额外的数据字段或更改广播方式。

- 在commassit.py中的`make_data_message`函数可以添加或修改广播的数据内容
- 在客户端脚本中相应地更新显示逻辑