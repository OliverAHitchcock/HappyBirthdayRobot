from enum import Enum
import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

current_directory = os.getcwd()
images_directory = os.path.join(current_directory, "modules/supervisor/images/")
load_dotenv(Path(f"{current_directory}/.env"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(GEMINI_API_KEY)

class State(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PICK_UP_CANDLE = "pick_up_candle"
    LIGHT_CANDLE = "light_candle"
    RETRACT_ARM = "retract_arm"
    ERROR = "error"

states = {
    State.IDLE: {
        "action": "start_robot"
    },
    State.RUNNING: {
        "action": "stop_robot"
    },
    State.PICK_UP_CANDLE: {
        "action": "pick_up_candle"
    },
    State.LIGHT_CANDLE: {
        "action": "light_candle"
    },
    State.RETRACT_ARM: {
        "action": "retract_arm"
    },
    State.ERROR: {
        "action": "reset_robot"
    }
}

from google import genai
from google.genai import types

# Initialize the GenAI client and specify the model
MODEL_ID = "gemini-robotics-er-1.5-preview"
PROMPT = """
          Point to no more than 10 items in the image. The label returned
          should be an identifying name for the object detected.
          The answer should follow the json format: [{"point": <point>,
          "label": <label1>}, ...]. The points are in [y, x] format
          normalized to 0-1000.
        """
client = genai.Client(api_key=GEMINI_API_KEY)

# Load your image
with open(os.path.join(images_directory, "test1.jpg"), 'rb') as f:
    image_bytes = f.read()

image_response = client.models.generate_content(
    model=MODEL_ID,
    contents=[
        types.Part.from_bytes(
            data=image_bytes,
            mime_type='image/jpeg',
        ),
        PROMPT
    ],
    config = types.GenerateContentConfig(
        temperature=0.5,
        thinking_config=types.ThinkingConfig(thinking_budget=0)
    )
)

print(image_response.text)




