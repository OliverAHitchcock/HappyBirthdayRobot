# HappyBirthdayRobot

A robotics hackathon project to automate the process of placing and lighting a birthday candle using a robot arm and supervisor logic. The project demonstrates asynchronous control, perception, and manual override via keyboard input.

https://www.canva.com/design/DAG27Vija9w/pFcQqAcDQsjhxfS3CfqlHQ/watch?utm_content=D[…]hare&utm_medium=link2&utm_source=uniquelinks&utlId=h2496b44a6b

## Features

- Hardware Hacked SO-101 seeedstudio robot arm
- Simulated robot API (`RobotAPI`) for placing and lighting candles
- Supervisor logic for orchestrating multi-step tasks
- Active monitoring and manual override: press any key to instantly light the candle
- Asynchronous concurrency: robot model and supervisor run in parallel
- Progress feedback: prints numbers every 0.1s during candle lighting to show async operation

## Hardware

### Environment

The environment is designed to be static and low-noise. White printer paper and poster boards surround the scene, providing high contrast for object detection and minimizing background distractions. An optical breadboard offers secure, rigid mounting points for the cameras and robotic arm.

Three cameras are used to view the scene:
- **Camera 1:** An FPV camera mounted on the robot arm for close-up views of the gripper, aiding fine manipulation.
- **Camera 2:** A webcam positioned high and to the side, providing an angled overview of the entire workspace.
- **Camera 3:** An Orbbec Gemini 2 depth camera provides medium-height side view.

### Robot Arm

The SO-101 robot arm by Seeed Studio serves as the base platform, with several modifications to enable candle lighting.

A custom 3D-printed mount holds the camera and provides locations for optional mirrors, enhancing the FPV camera's view and allowing attachment of a USB-controlled lighter.

In principle, the multiple-mirrors technique enables a single camera to capture three different angles, approximating the utility of a depth camera (at the cost of reduced field of view). In practice, the FPV camera used here has too narrow a field of view for the mirror technique to be effective; the required mirror angles sacrifice too much of the camera's usable view. A wider FOV or fisheye lens would make this approach more practical.

The USB-controlled lighter is a low-cost plasma arc lighter, hotwired to bypass its on-off switch and directly connect battery power to the plasma element when an external relay is activated. The relay is mounted on an Arduino board, which connects to the control computer via USB. A serial 9600 baud connection is used to trigger the relay and control the lighter.

The lighter is normal butane gas lighter that has been hacked for usb control. A simple custom 3D printed assembly holds the ligher and a servo motor. The servo motor is attached to a elliptical disk which when rotates depresses the ligher click mechanism, striking the flame. The servo motor is wired up to a relay which is mounted on an Arduino board, which connects to the control computer via USB. A serial 9600 baud connection is used to trigger the relay and turn the lighter on-off.

The lighter is a low-cost plasma arc lighter, hotwired to bypass its on-off switch and directly connect battery power to the plasma element when an external relay is activated. The relay is mounted on an Arduino board, which connects to the control computer via USB. A serial 9600 baud connection is used to trigger the relay and control the lighter.


## Robot Control

### Tutorial & Quickstart: Build and Run Your Own Birthday Robot

Follow these steps to get HappyBirthdayRobot running in minutes:

1. **Clone the repository**
   ```powershell
   git clone https://github.com/OliverAHitchcock/HappyBirthdayRobot.git
   cd HappyBirthdayRobot
   ```

2. **Create and activate a Python environment (recommended: uv)**
   ```powershell
   uv venv --python 3.10
   .\.venv\scripts\activate
   ```

3. **Install dependencies**
   (If you need extra packages, install them with uv pip)
   ```powershell
   uv pip install -U <package-name>
   ```

4. **Run the supervisor demo**
   ```powershell
   python modules/supervisor/async_supervisor.py
   ```

5. **Interact**
   - The robot will place and light a candle using real hardware and sensors.
   - During the lighting phase, press any key to instantly trigger the candle lighting via hardware control and cancel the lighting task.
   - Progress feedback prints every 0.1s to show the hardware model is running and supervised asynchronously.

#### What to Expect
The supervisor will print messages as it moves through each hardware-controlled task:
   - Placing the candle
   - Verifying placement with camera and vision model
   - Lighting the candle (prints numbers every 0.1s as the hardware runs)
   - Retracting the arm
During the lighting phase, press any key to instantly trigger the hardware lighter and see the supervisor react.

##### Example Output
```
--- SUPERVISOR: STARTING TASK 1: PLACE CANDLE ---
[Robot] Received command: run_model('place_candle')
[Robot] 'place_candle' model finished.
--- SUPERVISOR: TASK 1 COMPLETE ---
...existing output...
[Robot][light_candle] running... 1
[Robot][light_candle] running... 2
... (prints every 0.1s) ...
[Keyboard] Key pressed: a. Marking candle as lit.
[Keyboard] Cancelling 'light_candle' model due to manual key press.
[Supervisor] MONITOR: SUCCESS! Candle is lit.
[Supervisor] MONITOR: Cancelling 'light_candle' model now.
--- SUPERVISOR: TASK 3 COMPLETE (or cancelled) ---
--- SUPERVISOR: STARTING TASK 4: RETRACT ARM ---
...existing output...
```

##### Customization
- You can modify the supervisor or robot logic in `modules/supervisor/async_supervisor.py` to adapt to different hardware setups, sensors, or control strategies.
- Try changing the timing, adding new steps, or integrating with additional sensors and actuators!

---

### Folder Structure

```
modules/
  gr00t/
    justfile
  supervisor/
    async_supervisor.py
    supervisor.py
    test_query_gemini
    images/
      test1.jpg
```

### Requirements

- Python 3.10+
- Windows (uses `msvcrt` for keyboard input)
- [uv](https://github.com/astral-sh/uv) package manager (recommended for environment setup)

### Enhanced Supervision: Vision Model & Real-Time Feedback

Recent updates to the supervision script add real perception and feedback:

- **Vision Model Integration:** The supervisor now uses a generative AI vision model to analyze camera images and provide feedback for each robot state.
- **Camera Usage:** The robot captures images using your webcam to verify candle placement and flame status.
- **Detailed Robot State:** The robot tracks multiple state variables (e.g., `claw_has_candle`, `is_flame_lit`, `is_candle_in_cake`, `is_arm_retracted`, and `instructions`) for richer supervision and feedback.
- **Feedback Loop:** The supervisor queries the vision model after each action, parses the response, and updates the robot's state accordingly.

#### Example: Vision Model Feedback
After placing the candle, the supervisor captures an image and sends it to the vision model. The model returns a JSON response with detected objects, next state, and instructions, which the supervisor uses to decide the next action.

```python
# Capture image and run vision model
await take_picture(img_path)
response_json = await robot.query_vision_model(img_path)
robot.set_robot_state(response_json)
```

#### Updated Tutorial Steps
- The supervisor will now use your webcam to capture images and verify each step.
- Vision model feedback is used to determine if the candle is placed, lit, and if the arm should retract.
- The robot's state is updated in real time based on vision model output.

##### Example Output (Vision Model)
```
{"current_state": "pick_up_candle", "next_state": "light_candle", ...}
Instructions: The claw should light the candle next.
```

### Asynchronous Supervision: How It Works

HappyBirthdayRobot uses asynchronous programming to supervise real hardware tasks in real time. The supervisor coordinates and monitors multiple hardware actions concurrently, enabling instant intervention and robust control.

#### Why Asynchronous Supervision?
- **Responsiveness:** The supervisor can react instantly to events (like a candle being lit or a manual override) without waiting for long-running hardware tasks to finish.
- **Parallelism:** Hardware actions (e.g., lighting the candle) run in the background, while the supervisor checks sensors, listens for user input, and manages state transitions.
- **Safety and Control:** The supervisor can cancel or redirect hardware tasks based on perception or user actions, ensuring robust and flexible operation.

#### Implementation Details
- The supervisor and robot models are implemented as Python `async` coroutines using `asyncio`.
- The main robot model (e.g., `light_candle`) runs as an `asyncio.Task`, controlling hardware and printing progress every 0.1s.
- The supervisor launches a concurrent monitoring coroutine (`monitor_candle_lighting`) that:
   - Periodically checks if the candle is lit (using real sensors and vision model)
   - Listens for keyboard input in a background thread (using `msvcrt.getch` and `asyncio.to_thread`)
   - Cancels the robot's task immediately if the candle is lit or a key is pressed
- This design ensures the supervisor can always intervene, demonstrating true parallelism and control in hardware deployment.

##### Example: Supervisor and Model Running in Parallel
```python
# Start the robot model as a background task
light_candle_task = asyncio.create_task(robot.run_model("light_candle"))

# Start the supervisor monitor as a concurrent task
monitor_task = asyncio.create_task(monitor_candle_lighting(robot, light_candle_task))

# Wait for either to finish
await monitor_task
```

- While the robot prints progress every 0.1s, the supervisor can instantly respond to perception or user input, cancelling the hardware model and moving to the next step.

### Hackathon Goals

- Demonstrate async robotics control and supervision
- Enable manual intervention for rapid prototyping
- Provide clear feedback for parallel task execution

### License

See `LICENSE` for details.

### Quickstart

Follow these steps to get HappyBirthdayRobot running in minutes:

1. **Clone the repository**
   ```powershell
   git clone https://github.com/OliverAHitchcock/HappyBirthdayRobot.git
   cd HappyBirthdayRobot
   ```

2. **Create and activate a Python environment (recommended: uv)**
   ```powershell
   uv venv --python 3.10
   .\.venv\Scripts\activate
   ```

3. **Install dependencies**
   (If you need extra packages, install them with uv pip)
   ```powershell
   uv pip install -U <package-name>
   ```

4. **Run the supervisor demo**
   ```powershell
   python modules/supervisor/async_supervisor.py
   ```

5. **Interact**
   - The robot will simulate placing and lighting a candle.
   - During the lighting phase, press any key to instantly mark the candle as lit and cancel the lighting task.
   - Watch progress numbers print every 0.1s to confirm async concurrency.

---

### Tutorial: Build and Run Your Own Birthday Robot

#### 1. Project Overview
This project simulates a robot that can place and light a birthday candle, with a supervisor orchestrating the steps and monitoring progress. You can manually override the process by pressing any key during the lighting phase.

#### 2. Environment Setup
- Make sure you have Python 3.10+ and are on Windows (for keyboard input).
- Use the [uv](https://github.com/astral-sh/uv) package manager for fast environment creation and package installs.

#### 3. Running the Supervisor
- Open a terminal in the project root.
- Activate your environment and run:
  ```powershell
  python modules/supervisor/async_supervisor.py
  ```

#### 4. What to Expect
- The supervisor will print messages as it moves through each task:
  - Placing the candle
  - Verifying placement
  - Lighting the candle (prints numbers every 0.1s)
  - Retracting the arm
- During the lighting phase, press any key to instantly light the candle and see the supervisor react.

##### Example Output
```
--- SUPERVISOR: STARTING TASK 1: PLACE CANDLE ---
[Robot] Received command: run_model('place_candle')
[Robot] 'place_candle' model finished.
--- SUPERVISOR: TASK 1 COMPLETE ---
...existing output...
[Robot][light_candle] running... 1
[Robot][light_candle] running... 2
... (prints every 0.1s) ...
[Keyboard] Key pressed: a. Marking candle as lit.
[Keyboard] Cancelling 'light_candle' model due to manual key press.
[Supervisor] MONITOR: SUCCESS! Candle is lit.
[Supervisor] MONITOR: Cancelling 'light_candle' model now.
--- SUPERVISOR: TASK 3 COMPLETE (or cancelled) ---
--- SUPERVISOR: STARTING TASK 4: RETRACT ARM ---
...existing output...
```

#### 5. Customization
- You can modify the supervisor or robot logic in `modules/supervisor/async_supervisor.py`.
- Try changing the timing, adding new steps, or integrating with real hardware!

---

Happy hacking and happy birthday!
