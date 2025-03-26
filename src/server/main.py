import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from src.common.database import Base
from src.server.routers import voice, devices

# 加载环境变量
load_dotenv()

# 创建 FastAPI 应用
app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', 'data/uploads'))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 挂载静态文件服务
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 注册路由
app.include_router(voice.router)
app.include_router(devices.router)

# 初始化数据库
@app.on_event("startup")
async def init_db():
    engine = create_async_engine("sqlite+aiosqlite:///data/robot.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)