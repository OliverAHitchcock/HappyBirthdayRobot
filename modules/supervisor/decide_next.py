import asyncio
import time
import random
from typing import Optional
import sys
import cv2
from enum import Enum
import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from google import genai
from google.genai import types
import serial
import json_repair

current_directory = os.getcwd()
images_directory = os.path.join(current_directory, "modules/supervisor/images/")
# print("images directory", images_directory)
img_name = "frame.jpg"
linux = False
n_camera = 0
img_path = img_name
# if (not linux):
#     n_camera = 0
#     img_path = os.path.join(images_directory, img_name)
# Load the environment variables
_ = load_dotenv(Path(f"{current_directory}/.env"))

class State(Enum):
    IDLE = "idle"
    PLACE_CANDLE = "place_candle"
    LIGHT_CANDLE = "light_candle"
    RETRACT_ARM = "retract_arm"

GEMINI_API_KEY = "AIzaSyCUin4djDSjjYW30Q4nQpZ1-qfZPRhMjLs"
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

        If the image does not contain any of the objects of interest, return the current state and the next state as "IDLE", and false for all the other fields.

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
client = genai.Client(api_key=GEMINI_API_KEY)


def take_picture(img_path: str):
    # Open the default camera
    cam = cv2.VideoCapture(n_camera) # TODO change camera
    # print("Camera opened")
    # print("Waiting for 2 seconds...")
    time.sleep(2)
    # Capture one frame
    ret, frame = cam.read()
    # print("Frame captured")
    # Save the frame
    cv2.imwrite(img_path, frame)
    # Close the camera
    cam.release()

def query_vision_model(img_path: str) -> dict:
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
            )
        )
        # print(image_response.text)
        return json_repair.loads(image_response.text)

def picture_and_run_vision_model(use_api: bool = True) -> dict:
    # Open the default camera
    take_picture(img_path)
    # Run the vision model
    # response_json = run_vision_model(img_path)
    # Set the robot state
    if use_api:
        response_json = query_vision_model(img_path)
    else:
        response_json = {"current_state": State.IDLE, "next_state": State.LIGHT_CANDLE, "points": [], "claw_has_candle": False, "is_flame_lit": False, "is_candle_in_cake": True, "is_arm_retracted": False, "instructions": ""}
    # print(f"[Supervisor] Response JSON: {response_json}")
    return response_json


response = picture_and_run_vision_model(use_api=True)
# print(response)
if type(response) == dict and response is not None:
    if (response.get("is_candle_in_cake") == False or response.get("next_state") == State.PLACE_CANDLE):
        print("just run-candle-act")
        # print("say 'candle'")
    if (response.get("is_candle_in_cake") == True or response.get("next_state") == State.LIGHT_CANDLE):
        print("just run-lighter-act")
    if (response.get("is_flame_lit") == True):
        print("STOP")
else:
    print("just run-candle-act")
    # print("e 'idle'")

