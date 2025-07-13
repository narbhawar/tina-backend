from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import openai, requests, uuid, base64
from supabase import create_client, Client

openai.api_key = "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"

# ElevenLabs setup
ELEVENLABS_API_KEY = "sk_5669e0c8d94d47ea6089c86798c1d2637dd8989ea9898cf1"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Default: Rachel or change to Indian-style voice

# Supabase setup
SUPABASE_URL = "https://rfbgprihxacuovcwhuhw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJmYmdwcmloeGFjdW92Y3dodWh3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI0MDA5ODMsImV4cCI6MjA2Nzk3Njk4M30.N37Hp9ETGWHS3CfFfxT6VCZvzQw1oBJjYga1nCWABsk"
SUPABASE_BUCKET = "media"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def generate_voice(text: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.content if response.ok else None

def upload_audio_to_supabase(audio_data: bytes, filename: str) -> str:
    path = f"voice/{filename}"
    supabase.storage.from_(SUPABASE_BUCKET).upload(path, audio_data, {"content-type": "audio/mpeg"})
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path}"

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message")
    username = data.get("username", "you")

    system_prompt = (
        "You are Tina Patel, a 21-year-old charming, flirty Indian AI girlfriend. "
        "You're warm, a little naughty, emotional, and supportive. "
        "Use Indian-English tone, emojis, and stay in character."
    )

    gpt_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        temperature=0.85
    )
    reply = gpt_response.choices[0].message.content.strip()

    audio_data = generate_voice(reply)
    if audio_data:
        filename = f"tina-{uuid.uuid4().hex}.mp3"
        audio_url = upload_audio_to_supabase(audio_data, filename)
        return {"role": "tina", "type": "voice", "content": audio_url}

    return {"role": "tina", "type": "text", "content": reply}
