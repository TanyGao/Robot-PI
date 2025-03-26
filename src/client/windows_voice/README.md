# Windows Voice Client

这是一个基于 PySide6 的 Windows 语音客户端实现，用于与服务器进行语音交互。

## 功能特点

- 语音录制和播放
- 实时语音识别
- AI 对话响应
- 设备状态管理

## 依赖安装

```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

## 配置

在项目根目录创建 `.env` 文件：

```env
SERVER_URL=http://localhost:8000
DEVICE_NAME=Windows_Voice_Client
DATA_DIR=data
UPLOAD_DIR=data/uploads
```

## 运行

```bash
python -m src.client.windows_voice.main
```

## 使用说明

1. 启动应用后，会自动注册设备并连接服务器
2. 按住 "Press to Talk" 按钮进行录音
3. 松开按钮后，录音将被发送到服务器进行处理
4. 服务器返回的语音响应将自动播放
5. 对话历史将显示在界面上