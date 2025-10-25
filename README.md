# HappyBirthdayRobot

A robotics hackathon project to automate the process of placing and lighting a birthday candle using a simulated robot and supervisor logic. The project demonstrates asynchronous control, perception, and manual override via keyboard input.

## Features

- Simulated robot API (`RobotAPI`) for placing and lighting candles
- Supervisor logic for orchestrating multi-step tasks
- Active monitoring and manual override: press any key to instantly light the candle
- Asynchronous concurrency: robot model and supervisor run in parallel
- Progress feedback: prints numbers every 0.1s during candle lighting to show async operation

## Folder Structure

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

## Requirements

- Python 3.10+
- Windows (uses `msvcrt` for keyboard input)
- [uv](https://github.com/astral-sh/uv) package manager (recommended for environment setup)

## Setup

1. Create and activate a Python environment (recommended: use `uv`):

   ```powershell
   uv venv --python 3.10
   .\.venv\Scripts\activate
   ```

2. Install dependencies (if any):

   ```powershell
   uv pip install -U <package-name>
   ```

## Running the Supervisor

Navigate to the project root and run:

```powershell
python modules/supervisor/async_supervisor.py
```

- The robot will simulate placing and lighting a candle.
- During the lighting phase, press any key to instantly mark the candle as lit and cancel the lighting task.
- Progress numbers print every 0.1s to show the async model is running.

## How It Works

- The supervisor orchestrates a sequence: place candle → verify placement → light candle (with monitoring) → retract arm.
- The robot's `light_candle` model runs for 30 seconds, printing progress every 0.1s.
- The supervisor monitors for the candle being lit, either by perception or manual keypress.
- Manual override: press any key to flip the candle lit variable and cancel the lighting task.

## Asynchronous Supervision: How It Works

A key innovation in HappyBirthdayRobot is its use of asynchronous programming to supervise robotic models in real time. This approach allows the supervisor to monitor, intervene, and coordinate multiple tasks concurrently—just like a real-world robotics system.

### Why Asynchronous Supervision?
- **Responsiveness:** The supervisor can react instantly to events (like a candle being lit or a manual override) without waiting for long-running tasks to finish.
- **Parallelism:** Robot models (e.g., lighting the candle) run in the background, while the supervisor checks sensors, listens for user input, and manages state transitions.
- **Safety and Control:** The supervisor can cancel or redirect tasks based on perception or user actions, ensuring robust and flexible operation.

### Implementation Details
- The supervisor and robot models are implemented as Python `async` coroutines using `asyncio`.
- The main robot model (e.g., `light_candle`) runs as an `asyncio.Task`, simulating a long-running process with progress prints every 0.1s.
- The supervisor launches a concurrent monitoring coroutine (`monitor_candle_lighting`) that:
  - Periodically checks if the candle is lit (via simulated perception)
  - Listens for keyboard input in a background thread (using `msvcrt.getch` and `asyncio.to_thread`)
  - Cancels the robot's task immediately if the candle is lit or a key is pressed
- This design ensures the supervisor can always intervene, demonstrating true parallelism and control.

#### Example: Supervisor and Model Running in Parallel
```python
# Start the robot model as a background task
light_candle_task = asyncio.create_task(robot.run_model("light_candle"))

# Start the supervisor monitor as a concurrent task
monitor_task = asyncio.create_task(monitor_candle_lighting(robot, light_candle_task))

# Wait for either to finish
await monitor_task
```

- While the robot prints progress every 0.1s, the supervisor can instantly respond to perception or user input, cancelling the model and moving to the next step.

## Hackathon Goals

- Demonstrate async robotics control and supervision
- Enable manual intervention for rapid prototyping
- Provide clear feedback for parallel task execution

## License

See `LICENSE` for details.

## Quickstart

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

## Tutorial: Build and Run Your Own Birthday Robot

### 1. Project Overview
This project simulates a robot that can place and light a birthday candle, with a supervisor orchestrating the steps and monitoring progress. You can manually override the process by pressing any key during the lighting phase.

### 2. Environment Setup
- Make sure you have Python 3.10+ and are on Windows (for keyboard input).
- Use the [uv](https://github.com/astral-sh/uv) package manager for fast environment creation and package installs.

### 3. Running the Supervisor
- Open a terminal in the project root.
- Activate your environment and run:
  ```powershell
  python modules/supervisor/async_supervisor.py
  ```

### 4. What to Expect
- The supervisor will print messages as it moves through each task:
  - Placing the candle
  - Verifying placement
  - Lighting the candle (prints numbers every 0.1s)
  - Retracting the arm
- During the lighting phase, press any key to instantly light the candle and see the supervisor react.

#### Example Output
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

### 5. Customization
- You can modify the supervisor or robot logic in `modules/supervisor/async_supervisor.py`.
- Try changing the timing, adding new steps, or integrating with real hardware!

---

Happy hacking and happy birthday!
