from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import openai, requests, uuid, re, datetime
from pymongo import MongoClient
from supabase import create_client, Client

# === KEYS ===
openai.api_key = "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"
ELEVENLABS_API_KEY = "sk_5669e0c8d94d47ea6089c86798c1d2637dd8989ea9898cf1"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"

SUPABASE_URL = "https://rfbgprihxacuovcwhuhw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJmYmdwcmloeGFjdW92Y3dodWh3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI0MDA5ODMsImV4cCI6MjA2Nzk3Njk4M30.N37Hp9ETGWHS3CfFfxT6VCZvzQw1oBJjYga1nCWABsk"
SUPABASE_BUCKET = "media"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === MONGO ===
MONGO_URI = "mongodb+srv://Tina:tina123@clustertina.nntbqqx.mongodb.net/?retryWrites=true&w=majority&appName=Clustertina"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["tina"]
sessions = db["sessions"]
users = db["users"]
drops = db["drops"]
drop_track = db["drop_track"]

# === APP ===
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# === ROUTES ===

@app.get("/admin/user_memory")
def memory_summary(user_id: str):
    one_week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    chats = list(sessions.find({"user_id": user_id, "timestamp": {"$gte": one_week_ago}}))
    if not chats:
        return {"user_id": user_id, "summary": "No chats this week."}
    transcript = "\n".join([f"You: {c['message']}\nTina: {c['reply']}" for c in chats])
    prompt = "Summarize this conversation into a memory Tina would remember:\n" + transcriptr:"
    gpt_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    summary = gpt_response.choices[0].message.content.strip()
    return {"user_id": user_id, "summary": summary}

@app.post("/admin/add_drop")
async def add_drop(req: Request):
    data = await req.json()
    drop = {
        "type": data.get("type"),
        "content": data.get("content"),
        "tags": data.get("tags", []),
        "unlock_type": data.get("unlock_type", "free"),
        "schedule_time": data.get("schedule_time"),
        "created_at": datetime.datetime.utcnow()
    }
    drops.insert_one(drop)
    return {"status": "ok", "drop": drop}

@app.get("/drops/next_drop")
def get_next_drop(user_id: str):
    paid = users.find_one({"user_id": user_id, "is_paid": True}) is not None
    delivered_ids = set(d["drop_id"] for d in drop_track.find({"user_id": user_id}))
    now = datetime.datetime.utcnow()

    query = {
        "$and": [
            {"_id": {"$nin": list(delivered_ids)}},
            {"$or": [
                {"unlock_type": "free"},
                {"unlock_type": "paid", "$expr": {"$eq": [paid, True]}},
                {"unlock_type": "date", "schedule_time": {"$lte": now}}
            ]}
        ]
    }

    drop = drops.find_one(query)
    if not drop:
        return {"status": "none", "message": "No new drops"}

    drop_track.insert_one({
        "user_id": user_id,
        "drop_id": drop["_id"],
        "timestamp": now
    })

    return {"status": "ok", "drop": {
        "type": drop["type"],
        "content": drop["content"],
        "tags": drop.get("tags", [])
    }}
