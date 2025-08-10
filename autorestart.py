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
            # Fetch latest repo info without merging
            print("Checking for remote changes...")
            subprocess.run(["git", "fetch", "origin"], cwd=script_dir)

            # Get list of changed files between local HEAD and remote
            changed_files_process = subprocess.run(
                ["git", "diff", "--name-only", "HEAD", "origin/main"],
                cwd=script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            changed_files = changed_files_process.stdout.strip().split("\n") if changed_files_process.stdout.strip() else []

            # Decide whether to pull
            if changed_files == ["qotd.json"] or changed_files == []:
                print("Only qotd.json changed remotely or no changes at all. Skipping git pull.")
            else:
                # If qotd.json is locally modified, stash it before pull
                local_qotd_changed = subprocess.run(
                    ["git", "diff", "--quiet", "qotd.json"],
                    cwd=script_dir
                ).returncode != 0

                if local_qotd_changed:
                    print("Stashing local qotd.json changes...")
                    subprocess.run(["git", "stash", "push", "qotd.json"], cwd=script_dir)

                print("Pulling latest changes from git repository...")
                git_process = subprocess.run(
                    ["git", "pull"],
                    cwd=script_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                if git_process.returncode == 0:
                    print(f"Git pull successful:\n{git_process.stdout.strip()}")
                else:
                    print(f"Git pull failed:\n{git_process.stderr.strip()}")
                    print("Continuing with existing code...")

                # Restore qotd.json if stashed
                if local_qotd_changed:
                    print("Restoring local qotd.json changes...")
                    subprocess.run(["git", "stash", "pop"], cwd=script_dir)

            # Run the main bot script
            print("Starting bot...")
            process = subprocess.run(command, cwd=script_dir)
            print(f"Bot exited with code: {process.returncode}. Restarting in 5 seconds...")
            time.sleep(5)

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
