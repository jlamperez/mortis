import os
import json
import requests

from pathlib import Path
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")  # carga variables del .env (si existe)

API_KEY = os.getenv("MULTIVERSE_COMPACTIFAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.compactif.ai/v1/chat/completions")

SYSTEM = (
"You are Mortis, a mischievous Halloween spirit in a robotic arm. "
"Return structured outputs via function call when available."
)

TOOLS = [{
  "type":"function",
  "function":{
    "name":"perform_mortis_act",
    "description":"Return Mortis output in a structured way.",
    "parameters":{
      "type":"object",
      "properties":{
        "message":{"type":"string","maxLength":120,
                   "description":"One in-character line, <=30 words, no emojis/markdown."},
        "mood":{"type":"string","enum":["ominous","playful","angry","nervous","triumphant","mischievous","sinister","curious","neutral"]},
        "gesture":{"type":"string","enum":["idle","wave","point_left","point_right","grab","drop"]}
      },
      "required":["message","mood","gesture"],
      "additionalProperties": False
    }
  }
}]

def ask_mortis(user_msg: str, model_name:str):
    print(model_name)
    headers = {"Content-Type":"application/json","Authorization":f"Bearer {API_KEY}"}
    data = {
        "model": model_name,
        # "model": "cai-llama-4-scout-slim",
        "messages": [
            {"role":"system","content": SYSTEM},
            {"role":"user","content": user_msg}
        ],
        "tools": TOOLS,
        "tool_choice": {"type":"function","function":{"name":"perform_mortis_act"}},  # fuerza tool
        "temperature": 0.2
    }
    r = requests.post(API_BASE_URL, headers=headers, json=data, timeout=30)
    r.raise_for_status()
    choice = r.json()["choices"][0]["message"]

    tcalls = choice.get("tool_calls") or []
    if tcalls:
        args = json.loads(tcalls[0]["function"]["arguments"])
        message = (args.get("message") or "").strip()
        mood = (args.get("mood") or "ominous").strip()
        gesture = (args.get("gesture") or "idle").strip()
        # if gesture not in ALLOWED: gesture = "idle"

        # print("=== Mortis says ===")
        # print(message or "...")
        # print(json.dumps({"mood": mood, "gesture": gesture}, ensure_ascii=False))

        # move_arm(gesture)
        return message, mood, gesture


if __name__ == "__main__":
    ask_mortis("Mortis, someone is entering the lab… act!")
    ask_mortis("Introduce yourself with a sinister bow.")
    ask_mortis("Grab the cursed vial and then release it.")