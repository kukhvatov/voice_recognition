import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import whisper
from pydub import AudioSegment
import tempfile
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_SIZE = os.getenv("MODEL_SIZE", "base")
model = None


@app.on_event("startup")
async def load_model():
    global model
    model = whisper.load_model(MODEL_SIZE)


def convert_to_wav(input_path: str) -> str:
    audio = AudioSegment.from_file(input_path)
    wav_path = f"{tempfile.gettempdir()}/{uuid.uuid4()}.wav"
    audio.set_frame_rate(16000).set_channels(1).export(wav_path, format="wav")
    return wav_path


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    allowed_formats = ["mp3", "wav", "aac", "ogg", "flac", "m4a"]
    file_ext = file.filename.split(".")[-1].lower()

    if file_ext not in allowed_formats:
        raise HTTPException(400, "Unsupported file format")

    try:
        temp_path = f"{tempfile.gettempdir()}/{uuid.uuid4()}.{file_ext}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        audio_path = convert_to_wav(temp_path) if file_ext != "wav" else temp_path
        if file_ext != "wav":
            os.remove(temp_path)

        result = model.transcribe(
            audio_path,
            language="ru" if "ru" in file.filename.lower() else None,
            fp16=False,
            initial_prompt="Стиль с пунктуацией"
        )

        transcript_text = ""
        for i, segment in enumerate(result["segments"], 1):
            transcript_text += f"Реплика {i}\n{segment['text'].strip()}\n\n"

        transcript_text = transcript_text.strip()

        os.remove(audio_path)

        return Response(content=transcript_text, media_type="text/plain; charset=utf-8")

    except Exception as e:
        raise HTTPException(500, f"Processing error: {str(e)}")