from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import openai, requests, uuid, re, datetime
from pymongo import MongoClient
from supabase import create_client, Client

# === KEYS ===
openai.api_key = "YOUR_OPENAI_KEY"
ELEVENLABS_API_KEY = "YOUR_ELEVENLABS_KEY"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"

SUPABASE_URL = "https://rfbgprihxacuovcwhuhw.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"
SUPABASE_BUCKET = "media"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === MONGO ===
MONGO_URI = "mongodb+srv://Tina:tina123@clustertina.nntbqqx.mongodb.net/?retryWrites=true&w=majority&appName=Clustertina"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["tina"]
sessions = db["sessions"]
users = db["users"]

# === APP ===
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def generate_voice(text: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.8}
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.content if response.ok else None

def upload_to_supabase(data: bytes, path: str, content_type: str) -> str:
    supabase.storage.from_(SUPABASE_BUCKET).upload(path, data, {"content-type": content_type})
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path}"

def generate_image(prompt: str) -> str:
    dalle_response = openai.Image.create(
        prompt=prompt,
        model="dall-e-3",
        size="1024x1024",
        response_format="url"
    )
    return dalle_response['data'][0]['url']

def download_image(url: str) -> bytes:
    return requests.get(url).content

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message")
    user_id = data.get("user_id", "anon")

    # Check if user is paid
    paid_user = users.find_one({"user_id": user_id, "is_paid": True})

    system_prompt = (
        "You are Tina Patel, a 21-year-old charming, flirty Indian AI girlfriend. "
        "You're warm, loving, a bit naughty, and very expressive. Use emojis, flirt, and describe photos if needed."
    )

    gpt_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": message}],
        temperature=0.85
    )
    reply = gpt_response.choices[0].message.content.strip()

    log_entry = {
        "user_id": user_id,
        "message": message,
        "reply": reply,
        "timestamp": datetime.datetime.utcnow()
    }

    if paid_user and re.search(r"photo|pic|selfie|look|send.*image", reply, re.IGNORECASE):
        prompt = "A cute, flirty 21-year-old Indian girl named Tina, warm smile, looking at camera, casual indoor selfie, soft lighting, realistic photo style"
        image_url = generate_image(prompt)
        image_bytes = download_image(image_url)
        filename = f"tina-{uuid.uuid4().hex}.png"
        uploaded_url = upload_to_supabase(image_bytes, f"image/{filename}", "image/png")
        log_entry["type"] = "image"
        log_entry["media_url"] = uploaded_url
        sessions.insert_one(log_entry)
        return {"role": "tina", "type": "image", "content": uploaded_url}

    if paid_user:
        audio_data = generate_voice(reply)
        if audio_data:
            filename = f"tina-{uuid.uuid4().hex}.mp3"
            audio_url = upload_to_supabase(audio_data, f"voice/{filename}", "audio/mpeg")
            log_entry["type"] = "voice"
            log_entry["media_url"] = audio_url
            sessions.insert_one(log_entry)
            return {"role": "tina", "type": "voice", "content": audio_url}

    log_entry["type"] = "text"
    sessions.insert_one(log_entry)
    return {"role": "tina", "type": "text", "content": reply}

@app.get("/unlock")
def unlock(user_id: str = Query(...)):
    users.update_one({"user_id": user_id}, {"$set": {"is_paid": True}}, upsert=True)
    return {"status": "success", "message": f"Tina unlocked for {user_id}!"}
