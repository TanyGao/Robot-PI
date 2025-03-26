import sys
import os
import logging
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import wave
import pyaudio
import aiohttp
from dotenv import load_dotenv
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from qasync import QEventLoop

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 配置
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:8000')
DEVICE_NAME = os.getenv('DEVICE_NAME', 'Windows_Voice_Client')
DATA_DIR = Path(os.getenv('DATA_DIR', 'data'))
UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', 'data/uploads'))

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.is_recording = False
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
    def start_recording(self):
        self.frames = []
        self.is_recording = True
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self._callback
        )
        self.stream.start_stream()
        
    def _callback(self, in_data, frame_count, time_info, status):
        if self.is_recording:
            self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    def stop_recording(self):
        if self.stream:
            self.is_recording = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            return self.save_recording()
        return None
    
    def save_recording(self):
        if not self.frames:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = UPLOAD_DIR / f"recording_{timestamp}.wav"
        
        with wave.open(str(filename), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.frames))
            
        return filename
        
    def __del__(self):
        self.audio.terminate()

class VoiceClientWindow(QMainWindow):
    recording_started = Signal()
    recording_stopped = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.recorder = AudioRecorder()
        self.device_id = None
        self.session = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Voice Client')
        self.setGeometry(100, 100, 600, 400)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        self.status_label = QLabel('Ready')
        layout.addWidget(self.status_label)
        
        # 录音按钮
        self.record_button = QPushButton('Press to Talk')
        self.record_button.pressed.connect(self.start_recording)
        self.record_button.released.connect(self.stop_recording)
        layout.addWidget(self.record_button)
        
        # 对话历史文本区域
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        layout.addWidget(self.history_text)
        
        # 连接信号
        self.recording_started.connect(self.on_recording_started)
        self.recording_stopped.connect(self.on_recording_stopped)
        
    async def init_async(self):
        self.session = aiohttp.ClientSession()
        await self.register_device()
        
    async def cleanup(self):
        if self.session:
            await self.session.close()
            
    def start_recording(self):
        self.recorder.start_recording()
        self.recording_started.emit()
        
    def stop_recording(self):
        filename = self.recorder.stop_recording()
        if filename:
            self.recording_stopped.emit(str(filename))
            
    def on_recording_started(self):
        self.status_label.setText('Recording...')
        self.record_button.setStyleSheet('background-color: red;')
        
    def on_recording_stopped(self, filename):
        self.status_label.setText('Processing...')
        self.record_button.setStyleSheet('')
        asyncio.create_task(self.process_recording(filename))
        
    async def register_device(self):
        try:
            async with self.session.post(
                f"{SERVER_URL}/devices/register",
                json={"name": DEVICE_NAME, "status": "online"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.device_id = str(data.get('id'))
                    logger.info(f"Device registered with ID: {self.device_id}")
                else:
                    logger.error(f"Failed to register device: {await response.text()}")
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            
    async def update_device_status(self):
        if not self.device_id:
            return
            
        try:
            async with self.session.post(
                f"{SERVER_URL}/devices/{self.device_id}/status",
                json={"status": "online"}
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to update device status: {await response.text()}")
        except Exception as e:
            logger.error(f"Error updating device status: {e}")
            
    async def process_recording(self, filename):
        if not self.device_id:
            self.status_label.setText('Error: Device not registered')
            return
            
        try:
            # 上传音频文件
            with open(filename, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('audio', f)
                form.add_field('device_id', self.device_id)
                
                async with self.session.post(
                    f"{SERVER_URL}/voice/process",
                    data=form
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        text = result.get('text', '')
                        response_text = result.get('response', '')
                        audio_url = result.get('audio_url', '')
                        
                        # 更新对话历史
                        self.history_text.append(f"You: {text}")
                        self.history_text.append(f"AI: {response_text}")
                        self.history_text.append("---")
                        
                        # 播放响应音频
                        if audio_url:
                            await self.play_response_audio(audio_url)
                            
                        self.status_label.setText('Ready')
                    else:
                        error_text = await response.text()
                        self.status_label.setText(f'Error: {error_text}')
                        logger.error(f"Server error: {error_text}")
        except Exception as e:
            self.status_label.setText('Error occurred')
            logger.error(f"Error processing recording: {e}")
            
    async def play_response_audio(self, audio_url):
        try:
            async with self.session.get(f"{SERVER_URL}{audio_url}") as response:
                if response.status == 200:
                    audio_data = await response.read()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    temp_file = DATA_DIR / f"response_{timestamp}.wav"
                    
                    with open(temp_file, 'wb') as f:
                        f.write(audio_data)
                        
                    # 使用 pyaudio 播放音频
                    wf = wave.open(str(temp_file), 'rb')
                    p = pyaudio.PyAudio()
                    
                    def callback(in_data, frame_count, time_info, status):
                        data = wf.readframes(frame_count)
                        return (data, pyaudio.paContinue)
                    
                    stream = p.open(
                        format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        stream_callback=callback
                    )
                    
                    stream.start_stream()
                    
                    while stream.is_active():
                        await asyncio.sleep(0.1)
                        
                    stream.stop_stream()
                    stream.close()
                    wf.close()
                    p.terminate()
                    
                    # 删除临时文件
                    os.remove(temp_file)
        except Exception as e:
            logger.error(f"Error playing response audio: {e}")

async def run_app():
    app = QApplication(sys.argv)
    window = VoiceClientWindow()
    window.show()
    
    try:
        await window.init_async()
        
        # 创建定时器用于状态更新
        timer = QTimer()
        timer.timeout.connect(lambda: asyncio.create_task(window.update_device_status()))
        timer.start(60000)  # 每60秒更新一次状态
        
        # 等待应用程序退出
        while True:
            app.processEvents()
            await asyncio.sleep(0.1)
            if not window.isVisible():
                break
                
    except Exception as e:
        logging.error(f"Application error: {e}")
        raise
    finally:
        # 清理资源
        await window.cleanup()
        app.quit()

def main():
    try:
        loop = QEventLoop()
        asyncio.set_event_loop(loop)
        
        with loop:
            loop.run_until_complete(run_app())
    except Exception as e:
        logging.error(f"Main error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()