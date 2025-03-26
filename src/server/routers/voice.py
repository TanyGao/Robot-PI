import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.common.database import get_async_session, Conversation
from src.common.voice_service import VoiceService
from src.server.ai.education import EducationAI

router = APIRouter(prefix="/voice")
voice_service = VoiceService()
ai_service = EducationAI()

@router.post("/process")
async def process_voice(
    audio: UploadFile,
    device_id: str = Form(...),
    session: AsyncSession = Depends(get_async_session)
):
    # 保存上传的音频文件
    upload_dir = Path(os.getenv('UPLOAD_DIR', 'data/uploads'))
    audio_path = upload_dir / audio.filename
    
    with open(audio_path, 'wb') as f:
        content = await audio.read()
        f.write(content)
        
    try:
        # 语音识别
        text = await voice_service.recognize_speech(audio_path)
        
        # 获取 AI 响应
        response = await ai_service.get_response(text)
        
        # 语音合成
        response_audio = await voice_service.synthesize_speech(response, upload_dir)
        
        # 保存对话记录
        conversation = Conversation(
            device_id=int(device_id),
            user_input=text,
            ai_response=response
        )
        session.add(conversation)
        await session.commit()
        
        return {
            "text": text,
            "response": response,
            "audio_url": f"/uploads/{response_audio.name}" if response_audio else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理上传的音频文件
        os.remove(audio_path)