from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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
    return {"role": "tina", "type": "text", "content": f"You said: {message} ❤️"}
