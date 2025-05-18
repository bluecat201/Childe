import subprocess
import time
import os
import asyncio
import discord
from childe import sync_commands, bot

async def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    command = ["python3", "childe.py"]
    
    while True:
        try:
            # Perform git pull before running the script
            print("Pulling latest changes from git repository...")
            git_process = subprocess.run(
                ["git", "pull"],
                cwd=script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if git_process.returncode == 0:
                print(f"Git pull successful: {git_process.stdout.strip()}")
            else:
                print(f"Git pull failed: {git_process.stderr.strip()}")
                print("Continuing with existing code...")
            
            # Run the main bot script
            print("Starting bot...")
            process = subprocess.run(command, cwd=script_dir)
            print(f"Bot exited with code: {process.returncode}. Restarting in 5 seconds...")
            time.sleep(5)  # Pause before restart
            
            # Ensure commands are force-loaded after restart
            await sync_commands(bot)
            
        except KeyboardInterrupt:
            print("Auto-restart terminated by user.")
            break
        except Exception as e:
            print(f"Error occurred: {e}. Restarting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
