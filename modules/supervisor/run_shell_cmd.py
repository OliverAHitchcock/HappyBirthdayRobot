import subprocess
import sys

import asyncio


async def run_shell_command_async(cmd):
    print(cmd)
    try:
        process = await asyncio.create_subprocess_shell(
            " ".join(cmd),
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.STDOUT
        )
        assert process.stdout
        async for line in process.stdout:
            print("robot:", line.decode().rstrip())
        return await process.wait()
    except FileNotFoundError as e:
        # Print the standard output (if any)
        print(e)
        # if e.stdout:
        #     print("\n[Standard Output]:")
        #     print(e.stdout)
            
        # # Print the standard error (most likely where the error message is)
        # if e.stderr:
        #     print("\n[Standard Error]:")
        #     print(e.stderr)

def run_shell_command(command_list):
    """
    Runs a shell command and captures its output and error.

    Args:
        command_list: A list of strings representing the command and its arguments.
                      e.g., ['ls', '-l'] or ['ping', 'google.com']
    
    Returns:
        None. Prints the output or error.
    """
    print(f"--- Running command: {' '.join(command_list)} ---")
    
    try:
        # subprocess.run() is the modern and recommended way to run commands.
        # - capture_output=True: Captures stdout and stderr.
        # - text=True: Decodes stdout and stderr as text (using default encoding).
        # - check=True: Raises a CalledProcessError if the command returns
        #               a non-zero exit code (i.e., if it fails).
        result = subprocess.run(
            command_list, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # If the command was successful (exit code 0)
        print("\n--- Command Successful (Exit Code 0) ---")
        
        # Print the standard output
        if result.stdout:
            print("\n[Standard Output]:")
            print(result.stdout)
            
        # Print the standard error (less common for successful commands)
        if result.stderr:
            print("\n[Standard Error (while successful)]:")
            print(result.stderr)

    except subprocess.CalledProcessError as e:
        # This block runs if the command fails (non-zero exit code)
        print(f"\n--- Command Failed (Exit Code {e.returncode}) ---")
        
        # Print the standard output (if any)
        if e.stdout:
            print("\n[Standard Output]:")
            print(e.stdout)
            
        # Print the standard error (most likely where the error message is)
        if e.stderr:
            print("\n[Standard Error]:")
            print(e.stderr)
            
    except FileNotFoundError:
        # This block runs if the command itself isn't found
        print(f"\n--- Error: Command not found: '{command_list[0]}' ---")
        print("Please ensure the command is installed and in your system's PATH.")
        
    except Exception as e:
        # Catch any other unexpected errors
        print(f"\n--- An unexpected error occurred: {e} ---")

# --- Example Usage ---
if __name__ == "__main__":
    # Cross-platform example: list files in current directory
    if sys.platform == "win32":
        print("Running 'dir' on Windows...")
        run_shell_command(["cmd", "/c", "dir"])
    else:
        print("Running 'ls -l' on Linux/macOS...")
        run_shell_command(["ls", "-l"])

    print("\n" + "="*30 + "\n")

    # Cross-platform ping example
    if sys.platform == "win32":
        ping_command = ["ping", "-n", "1", "google.com"]
    else:
        ping_command = ["ping", "-c", "1", "google.com"]
    run_shell_command(ping_command)

    print("\n" + "="*30 + "\n")
