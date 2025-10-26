import asyncio
import time
import random
from typing import Optional
import sys
import cv2
# from cv2 import *
from enum import Enum
import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from helper import *
from google import genai
from google.genai import types
from supervisor import run_vision_model
import serial

if sys.platform.startswith('win'):
    import msvcrt
else:
    import getch

serial_port = '/dev/ttyACM2'

# Get current directory
current_directory = os.getcwd()
images_directory = os.path.join(current_directory, "modules/supervisor/images/")
img_name = "frame.jpg"
img_path = os.path.join(images_directory, img_name)
# Load the environment variables
load_dotenv(Path(f"{current_directory}/.env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
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
        
        Return the current state, next state of the robot claw, the points, and the instructions in the json format:
          {"current_state": <current_state>,
          {"next_state": <next_state>,
          "points": [{"point": <point>, "label": <label>}, ...],
          "claw_has_candle": <claw_has_candle>,
          "is_flame_lit": <is_flame_lit>,
          "is_candle_in_cake": <is_candle_in_cake>,
          "is_arm_retracted": <is_arm_retracted>,
          "instructions": <instructions>}

        If the image does not contain any of the objects of interest, return the current state and the next state as "IDLE", and false for all the other fields.
        """
client = genai.Client(api_key=GEMINI_API_KEY)

def read_single_key():
    if sys.platform.startswith('win'):
        return msvcrt.getch().decode('utf-8')
    else:
        return getch.getch().decode('utf-8')

async def take_picture(img_path: str):
    # Open the default camera
    cam = cv2.VideoCapture(0)
    print("Camera opened")
    print("Waiting for 2 seconds...")
    time.sleep(2)
    # Capture one frame
    ret, frame = cam.read()
    print("Frame captured")
    # Save the frame
    cv2.imwrite(img_path, frame)
    # Close the camera
    cam.release()

# --- Mock Gemini ER1.5 Robotics API ---
# This class simulates the robot's API, allowing us to build
# and test the supervisor logic.

class State(Enum):
    IDLE = "idle"
    PLACE_CANDLE = "place_candle"
    LIGHT_CANDLE = "light_candle"
    RETRACT_ARM = "retract_arm"

class RobotAPI:
    """
    A mock class simulating the Gemini ER1.5 robotics preview API.
    It provides asynchronous methods to run models and query sensors.
    """
    def __init__(self):
        # self.current_state = State.
        self.current_state = State.IDLE
        self._lighting_start_time: Optional[float] = None
        self.candle_is_actually_lit = False
        self.claw_has_candle = False
        self.is_flame_lit = False
        self.is_candle_in_cake = False
        self.is_arm_retracted = False
        self.instructions = ""
        print("RobotAPI initialized. State: idle")


    def set_robot_state(self, response_json: dict):
        if (type(response_json) != dict or response_json is None):
            return
        # self.next_state = response_json.get("next_state", State.IDLE)
        self.current_state = response_json.get("next_state", State.IDLE)
        self.claw_has_candle = response_json.get("claw_has_candle", False)
        self.is_flame_lit = response_json.get("is_flame_lit", False)
        self.is_candle_in_cake = response_json.get("is_candle_in_cake", False)
        self.is_arm_retracted = response_json.get("is_arm_retracted", False)
        self.instructions = response_json.get("instructions", "")
        
    async def run_model(self, model_name: str) -> bool:
        """
        Simulates the execution of a long-running robotics model.
        This is cancellable, which is critical for the "light_candle" task.
        """
        print(f"[Robot] Received command: run_model('{model_name}')")
        self.robot_state = f"running_{model_name}"
        
        try:
            if model_name == State.PLACE_CANDLE:
                # Simulate the time taken to place the candle

                duration = 10.0
                interval = 0.1
                steps = int(duration / interval)

                # Print a counter every `interval` seconds to simulate progress.
                for i in range(steps):
                    # Show which step we're on so output demonstrates concurrency.
                    print(f"[Robot][light_candle] running... {i+1}")
                    await asyncio.sleep(interval)
                print("[Robot] 'place_candle' model finished.")
                
            elif model_name == State.LIGHT_CANDLE:
                # This is the task we will actively supervise.
                # Simulate a long-running model that reports progress every 0.1s
                # so we can observe that the supervisor and model run in parallel.

                duration = 10.0
                interval = 0.1
                steps = int(duration / interval)

                # Print a counter every `interval` seconds to simulate progress.
                for i in range(steps):
                    # Show which step we're on so output demonstrates concurrency.
                    print(f"[Robot][light_candle] running... {i+1}")
                    await asyncio.sleep(interval)

                print("[Robot] 'light_candle' model timed out (finished naturally).")
                ser = serial.Serial(serial_port, 9600)  # open serial port
                print(ser.name)         # check which port was really used
                ser.write(b'1')     # write a string
                ser.close()             # close port

            elif model_name == State.RETRACT_ARM:
                await asyncio.sleep(4)
                print("[Robot] 'retract_arm' model finished. Arm is home.")

            self.robot_state = State.IDLE
            return True # Task completed successfully

        except asyncio.CancelledError:
            print(f"[Robot] 'run_model({model_name})' was CANCELLED by supervisor.")
            self.robot_state = State.IDLE
            # Simulate a brief period to safely stop the model
            await asyncio.sleep(1)
            self.robot_state = State.IDLE
            raise # Re-raise the exception so the supervisor knows it was cancelled

        finally:
            # Clean up state regardless of how the task ended
            if model_name == "light_candle":
                self._lighting_start_time = None

    def query_vision_model(self, img_path: str) -> dict:
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
        return json_repair.loads(image_response.text)


    async def picture_and_run_vision_model(self, use_api: bool = True) -> dict:
        # Open the default camera
        await take_picture(img_path)
        # Run the vision model
        # response_json = run_vision_model(img_path)
        # Set the robot state
        if use_api:
            response_json = self.query_vision_model(img_path)
            # response_json = run_vision_model(img_path)
            self.set_robot_state(response_json)
        else:
            response_json = {"current_state": State.IDLE, "next_state": State.LIGHT_CANDLE, "points": [], "claw_has_candle": False, "is_flame_lit": False, "is_candle_in_cake": True, "is_arm_retracted": False, "instructions": ""}
        print(f"[Supervisor] Response JSON: {response_json}")
        return response_json

# --- Supervisor Logic ---

async def monitor_general(
    robot: RobotAPI, 
    main_task: asyncio.Task, 
    check_interval: float = 5.0,
    function_to_check: callable=lambda x: x.is_candle_in_cake
):
    """
    Concurrent supervision task.
    Periodically checks the camera to see if the candle has been placed.
    Cancels the main task early if success is detected.
    """
    print(f"[Supervisor] Monitor started. Checking every {check_interval:.1f}s.")

    try:
        while not main_task.done():
            # Wait for either the interval to elapse or the task to finish early
            done, _ = await asyncio.wait(
                [main_task],
                timeout=check_interval
            )
            if done:  # main task completed early
                break

            print("[Supervisor] Checking camera for candle...")
            result = await robot.picture_and_run_vision_model()
            robot.set_robot_state(result)
            if function_to_check(robot):
                print("[Supervisor] ✅ Success, stopping main task.")
                main_task.cancel()
                break
            else:
                print("[Supervisor] ❌ Not success, continuing...")

    except asyncio.CancelledError:
        print("[Supervisor] Monitor was cancelled.")
        raise

    finally:
        print("[Supervisor] Monitor stopped.")


async def main():
    """
    The main Robotics Supervisor orchestration logic.
    """
    robot = RobotAPI()

    # TODO: Implement the FSM
    robot.current_state = State.PLACE_CANDLE
    is_first_time = True
    while True:
    # INSERT_YOUR_CODE
        # Finite State Machine for Supervising the Candle Task
        # States: IDLE -> PLACE_CANDLE -> VERIFY_PLACEMENT -> LIGHT_CANDLE -> RETRACT_ARM
        if is_first_time:
            print('back in main loop', robot.current_state)
        if robot.current_state == State.IDLE:
            response_json = await robot.picture_and_run_vision_model()
            if response_json is None or type(response_json) != dict or response_json.get("next_state") == State.IDLE:
                print("--- SUPERVISOR: No objects of interest found. ---")
                continue
            robot.set_robot_state(response_json)
            await asyncio.sleep(5)
            if robot.current_state != State.IDLE:
                is_first_time = True
                print("[Supervisor][FSM] Proceeding to place the candle.")
            
        elif robot.current_state == State.PLACE_CANDLE:
            if is_first_time:
                place_candle_task = asyncio.create_task(robot.run_model(State.PLACE_CANDLE))
                # 2. Create the concurrent monitoring task.
                #    We pass it a reference to the 'light_candle_task' so it can cancel it.
                # monitor_place_candle_task = asyncio.create_task(monitor_place_candle(robot, place_candle_task, check_interval=5.0))
                monitor_place_candle_task = asyncio.create_task(monitor_general(robot, place_candle_task, check_interval=5.0, function_to_check=lambda x: x.is_candle_in_cake))

                # 3. Wait for the monitoring task to complete.
                #    The monitor will exit when EITHER the candle is lit
                #    OR the 'place_candle' task finishes on its own.
                await monitor_place_candle_task
                    
                # 4. We must also 'await' the main task.
                #    - If it was cancelled, this will raise asyncio.CancelledError.
                #    - If it finished normally (timed out), this will return its result.
                #    This is crucial for proper exception handling.
                is_first_time = False
            try:
                await place_candle_task
            except asyncio.CancelledError:
                print("[Supervisor][FSM] 'place_candle_task' was cancelled due to interrupt or success.")
                robot.current_state = State.LIGHT_CANDLE
                is_first_time = True
                print("[Supervisor][FSM] Place candle process complete.")
            if robot.is_candle_in_cake:
                robot.current_state = State.LIGHT_CANDLE
                is_first_time = True
                print("[Supervisor][FSM] Candle is in the cake. Proceeding to light the candle.")

        elif robot.current_state == State.LIGHT_CANDLE:
            if is_first_time:
                light_candle_task = asyncio.create_task(robot.run_model(State.LIGHT_CANDLE))
                # monitor_task = asyncio.create_task(monitor_candle_lighting(robot, light_candle_task))
                monitor_task = asyncio.create_task(monitor_general(robot, light_candle_task, check_interval=5.0, function_to_check=lambda x: x.is_flame_lit))
                await monitor_task
                is_first_time = False
            try:
                await light_candle_task
            except asyncio.CancelledError:
                print("[Supervisor][FSM] 'light_candle_task' was cancelled due to interrupt or success.")
                print("[Supervisor][FSM] Candle light process complete.")
                robot.current_state = State.RETRACT_ARM
                is_first_time = True
                print("[Supervisor][FSM] Candle is lit. Proceeding to retract the arm.")
            if robot.is_flame_lit:
                robot.current_state = State.RETRACT_ARM
                is_first_time = True
                print("[Supervisor][FSM] Candle is lit. Proceeding to retract the arm.")

        elif robot.current_state == State.RETRACT_ARM:
            print("\n[Supervisor][FSM] State: RETRACT_ARM")
            await robot.run_model("retract_arm")
            print("[Supervisor][FSM] RETRACT_ARM complete. Mission accomplished!")
            break

        else:
            print(f"[Supervisor][FSM] Unknown state: {robot.current_state}")
            break
    # end TODO

if __name__ == "__main__":
    print("Starting Robotics Supervisor Program...")
    asyncio.run(main())
