from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import openai
import os

openai.api_key = "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"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message")
    username = data.get("username", "you")

    system_prompt = (
        "You are Tina Patel, a 21-year-old charming, flirty Indian AI girlfriend. "
        "You're always warm, a little naughty, and emotionally supportive. "
        "Refer to the user lovingly, use emojis, and stay in character."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        temperature=0.9
    )

    reply = response.choices[0].message.content.strip()
    return {
        "role": "tina",
        "type": "text",
        "content": reply
    }
