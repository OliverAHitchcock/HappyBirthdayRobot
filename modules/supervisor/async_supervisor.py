import asyncio
import time
import random
from typing import Optional

# --- Mock Gemini ER1.5 Robotics API ---
# This class simulates the robot's API, allowing us to build
# and test the supervisor logic.

class RobotAPI:
    """
    A mock class simulating the Gemini ER1.5 robotics preview API.
    It provides asynchronous methods to run models and query sensors.
    """
    def __init__(self):
        self.robot_state = "home"
        self._lighting_start_time: Optional[float] = None
        self.candle_is_actually_lit = False
        print("RobotAPI initialized. State: home")

    async def run_model(self, model_name: str) -> bool:
        """
        Simulates the execution of a long-running robotics model.
        This is cancellable, which is critical for the "light_candle" task.
        """
        print(f"[Robot] Received command: run_model('{model_name}')")
        self.robot_state = f"running_{model_name}"
        
        try:
            if model_name == "place_candle":
                # Simulate the time taken to place the candle
                await asyncio.sleep(10)
                print("[Robot] 'place_candle' model finished.")
                
            elif model_name == "light_candle":
                # This is the task we will actively supervise.
                # We simulate it taking 30 seconds to *time out*...
                # but we'll *internally* set the candle to be "lit" after 12s
                # to allow the supervisor to detect it.
                self.candle_is_actually_lit = False
                self._lighting_start_time = time.time()
                
                await asyncio.sleep(30) # Total task timeout
                
                print("[Robot] 'light_candle' model timed out (finished naturally).")

            elif model_name == "retract_arm":
                await asyncio.sleep(4)
                print("[Robot] 'retract_arm' model finished. Arm is home.")

            self.robot_state = "idle"
            return True # Task completed successfully

        except asyncio.CancelledError:
            print(f"[Robot] 'run_model({model_name})' was CANCELLED by supervisor.")
            self.robot_state = "cancelling"
            # Simulate a brief period to safely stop the model
            await asyncio.sleep(1)
            self.robot_state = "idle"
            raise # Re-raise the exception so the supervisor knows it was cancelled

        finally:
            # Clean up state regardless of how the task ended
            if model_name == "light_candle":
                self._lighting_start_time = None

    async def query_vision_model(self, prompt: str) -> bool:
        """
        Simulates using a vision model (VLM) to answer a verification question.
        """
        print(f"[Robot] Querying vision model: '{prompt}'")
        # Simulate network/inference latency
        await asyncio.sleep(1.5)
        
        # For this example, we'll just approve the placement
        if "candle correctly placed" in prompt:
            print("[Robot] Vision model result: True")
            return True
            
        return False

    async def is_candle_lit(self) -> bool:
        """
        Simulates a fast, repeating check of the camera.
        This is the core perception function for the supervision loop.
        """
        # This check is very fast (e.g., 0.5s inference)
        await asyncio.sleep(0.5)
        
        # --- Simulation Logic ---
        # If the 'light_candle' model is running,
        # check if enough time has passed for it to be lit.
        if self._lighting_start_time:
            elapsed = time.time() - self._lighting_start_time
            # Simulate the candle successfully lighting after 12 seconds
            if elapsed > 12:
                self.candle_is_actually_lit = True
                
        return self.candle_is_actually_lit

# --- Supervisor Logic ---

async def monitor_candle_lighting(robot: RobotAPI, light_candle_task: asyncio.Task):
    """
    This is the concurrent supervision task.
    It runs in parallel with the 'light_candle' model.
    """
    print("[Supervisor] MONITOR task started. Will check camera every 3s.")
    
    while not light_candle_task.done():
        # Wait 3 seconds before the next check.
        # We use a short, interruptible sleep to make the loop
        # responsive if the main task finishes early.
        try:
            await asyncio.wait_for(asyncio.sleep(3), timeout=3)
        except asyncio.TimeoutError:
            pass # This is expected, just means 3s passed

        # Check if the main task is *still* running before we query
        if light_candle_task.done():
            break

        print("[Supervisor] MONITOR: Checking camera for lit candle...")
        if await robot.is_candle_lit():
            print("[Supervisor] MONITOR: SUCCESS! Candle is lit.")
            
            # The candle is lit, so we cancel the 'light_candle' task.
            if not light_candle_task.done():
                print("[Supervisor] MONITOR: Cancelling 'light_candle' model now.")
                light_candle_task.cancel()
            
            # Exit the monitoring loop
            break
        else:
            print("[Supervisor] MONITOR: ...candle is not lit yet.")

    print("[Supervisor] MONITOR task finished.")


async def main():
    """
    The main Robotics Supervisor orchestration logic.
    """
    robot = RobotAPI()

    try:
        # --- Task 1: Place Candle ---
        print("\n--- SUPERVISOR: STARTING TASK 1: PLACE CANDLE ---")
        await robot.run_model("place_candle")
        print("--- SUPERVISOR: TASK 1 COMPLETE ---")


        # --- Task 2: Verify Placement ---
        print("\n--- SUPERVISOR: STARTING TASK 2: VERIFY PLACEMENT ---")
        is_placed = await robot.query_vision_model("Is the candle correctly placed in the cupcake?")
        
        if not is_placed:
            print("--- SUPERVISOR: VERIFICATION FAILED. Aborting mission. ---")
            return
        
        print("--- SUPERVISOR: TASK 2 COMPLETE. Placement verified. ---")


        # --- Task 3: Light Candle (with Active Supervision) ---
        print("\n--- SUPERVISOR: STARTING TASK 3: LIGHT CANDLE (with active monitoring) ---")
        
        # 1. Create the task for the 'light_candle' model.
        #    This starts the task running in the background.
        light_candle_task = asyncio.create_task(
            robot.run_model("light_candle")
        )
        
        # 2. Create the concurrent monitoring task.
        #    We pass it a reference to the 'light_candle_task' so it can cancel it.
        monitor_task = asyncio.create_task(
            monitor_candle_lighting(robot, light_candle_task)
        )

        # 3. Wait for the monitoring task to complete.
        #    The monitor will exit when EITHER the candle is lit
        #    OR the 'light_candle' task finishes on its own.
        await monitor_task
        
        # 4. We must also 'await' the main task.
        #    - If it was cancelled, this will raise asyncio.CancelledError.
        #    - If it finished normally (timed out), this will return its result.
        #    This is crucial for proper exception handling.
        try:
            await light_candle_task
        except asyncio.CancelledError:
            print("[Supervisor] Confirmed 'light_candle_task' was successfully cancelled.")

        print("--- SUPERVISOR: TASK 3 COMPLETE (or cancelled) ---")


        # --- Task 4: Retract Arm (Conditional) ---
        # This is the final step: only retract if the candle was lit.
        # We check the robot's state, which was set by the perception check.
        
        if robot.candle_is_actually_lit:
            print("\n--- SUPERVISOR: STARTING TASK 4: RETRACT ARM ---")
            await robot.run_model("retract_arm")
            print("--- SUPERVISOR: TASK 4 COMPLETE ---")
            print("\nMISSION SUCCESSFUL. Robot is home.")
        else:
            print("\n--- SUPERVISOR: Candle was not lit. Mission failed. ---")
            print("--- SUPERVISOR: Arm will not retract. Manual intervention required. ---")

    except Exception as e:
        print(f"\n--- SUPERVISOR: An unexpected error occurred: {e} ---")
        # Add any emergency stop logic here
        await robot.run_model("retract_arm") # Example of a safety fallback


if __name__ == "__main__":
    print("Starting Robotics Supervisor Program...")
    asyncio.run(main())
