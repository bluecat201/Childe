import subprocess
import time

def main():
    command = ["python3", "childe.py"]  # Nahraďte "vas_skript.py" názvem svého Python skriptu
    while True:
        try:
            print("Spouštím skript...")
            process = subprocess.run(command)
            print(f"Skript ukončen s kódem: {process.returncode}. Restart za 5 sekund...")
            time.sleep(5)  # Pauza před restartem
        except KeyboardInterrupt:
            print("Autorestart ukončen.")
            break
        except Exception as e:
            print(f"Nastala chyba: {e}. Restart za 5 sekund...")
            time.sleep(5)

if __name__ == "__main__":
    main()
