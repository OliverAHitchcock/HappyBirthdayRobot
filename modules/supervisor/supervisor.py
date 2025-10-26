from enum import Enum
import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from helper import *
from google import genai
from google.genai import types

current_directory = os.getcwd()
images_directory = os.path.join(current_directory, "modules/supervisor/images/")
load_dotenv(Path(f"{current_directory}/.env"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(GEMINI_API_KEY)

class State(Enum):
    IDLE = "idle"
    PICK_UP_CANDLE = "pick_up_candle"
    LIGHT_CANDLE = "light_candle"
    RETRACT_ARM = "retract_arm"
    ERROR = "error"

states = {
    State.IDLE: {
        "action": "start_robot"
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
}

# Initialize the GenAI client and specify the model
MODEL_ID = "gemini-robotics-er-1.5-preview"
PROMPT = """
          Point to no more than 10 items in the image. The label returned
          should be an identifying name for the object detected.
          The points are in [y, x] format
          normalized to 0-1000.

          The objects of interest are:
          - robot claw
          - lighter, attached to robot claw
          - candles
          - toy cake / cupcake

          You will provide feedback to submodels that execute robot claw movement.
          There are the following states the robot claw can take:
          - IDLE = "idle"
          - PICK_UP_CANDLE = "pick_up_candle"
          - LIGHT_CANDLE = "light_candle"
          - RETRACT_ARM = "retract_arm"
          Objective:
            - The claw should pick up the candle, place it in the cake.
            - The claw should light the candle.
            - The claw should retract the arm.
        You should direct the claw to complete the objective by outputting the next state.

        If the image does not contain any of the objects of interest, return the current state and the next state as "IDLE", and false for all the other fields.
          Return the current state, next state of the robot claw, the points, and the instructions in the json format:
          {"current_state": <current_state>,
          {"next_state": <next_state>,
          "points": [{"point": <point>, "label": <label>}, ...],
          "claw_has_candle": <claw_has_candle>,
          "is_flame_lit": <is_flame_lit>,
          "is_candle_in_cake": <is_candle_in_cake>,
          "is_arm_retracted": <is_arm_retracted>,
          "instructions": <instructions>}
        """

# cur_img = "in_cake.jpg"
client = genai.Client(api_key=GEMINI_API_KEY)


# Load your image
def run_vision_model(img_path: str):
    with open(img_path, 'rb') as f:
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
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            # tools=[types.Tool(code_execution=types.ToolCodeExecution)]
        )
    )

    # image_response = [
    #         {"point": [492, 292], "label": "toy cake / cupcake"},
    #         {"point": [507, 274], "label": "candles"},
    #         {"point": [374, 439], "label": "robot claw"},
    #         {"point": [247, 477], "label": "lighter, attached to robot claw"}]


    # print(parse_json(image_response.text))
    # 
    print(image_response.text)
    response_json = parse_json(image_response.text)
    return response_json
    print(response_json)
    print(type(response_json))


# response_json = {
#   "next_state": "pick_up_candle",
#   "points": [
#     {
#       "point": [643, 434],
#       "label": "robot claw"
#     },
#     {
#       "point": [666, 426],
#       "label": "lighter, attached to robot claw"
#     },
#     {
#       "point": [672, 426],
#       "label": "candles"
#     },
#     {
#       "point": [774, 465],
#       "label": "toy cake / cupcake"
#     }
#   ],
#   "instructions": "The robot claw is currently idle. The next step is to pick up the candle. The candle is located near the robot claw, on the white surface."
# }

# label_image(images_directory, cur_img, response_json.get("points", []))








