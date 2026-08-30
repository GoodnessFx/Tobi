from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from Tobi.memory.reminders_store import create_reminder, update_reminder_status, ReminderStatus, PlaybackMode, Recurrence
from Tobi.memory.reminders_store import AUDIO_DIR
import os

router = APIRouter(prefix="/api/v1/vscode", tags=["vscode_bridge"])

@router.post("/reminder")
async def api_create_reminder(content: str, due_at: float, is_alarm: bool = False, playback_mode: PlaybackMode = PlaybackMode.TOBI_VOICE, recurrence: Recurrence = Recurrence.NONE):
    try:
        reminder = create_reminder(content, due_at, is_alarm=is_alarm, playback_mode=playback_mode, recurrence=recurrence)
        return JSONResponse(content={"id": reminder.id, "status": "created"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reminder/{rem_id}/snooze")
async def api_snooze_reminder(rem_id: int, snooze_until: float):
    try:
        update_reminder_status(rem_id, ReminderStatus.SNOOZED)
        # TODO: store snooze_until in DB (not shown)
        return JSONResponse(content={"id": rem_id, "status": "snoozed"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reminder/{rem_id}/dismiss")
async def api_dismiss_reminder(rem_id: int):
    try:
        update_reminder_status(rem_id, ReminderStatus.DISMISSED)
        return JSONResponse(content={"id": rem_id, "status": "dismissed"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reminder/{rem_id}/voice")
async def api_upload_voice(rem_id: int, file: UploadFile = File(...)):
    try:
        dest_path = os.path.join(AUDIO_DIR, f"{rem_id}_{file.filename}")
        async with aiofiles.open(dest_path, "wb") as out:
            content = await file.read()
            await out.write(content)
        return JSONResponse(content={"id": rem_id, "voice": "saved"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
