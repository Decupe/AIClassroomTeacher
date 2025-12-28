import argparse
from pathlib import Path
from app.voice_id import register_student

def main():
    parser = argparse.ArgumentParser(description="Register a student's voice sample.")
    parser.add_argument("--name", type=str, help="Student name (e.g., Samuel)")
    parser.add_argument("--audio", type=str, help="Path to audio sample (wav/m4a)")
    args = parser.parse_args()

    name = (args.name or input("Student name: ").strip()).strip()
    audio = (args.audio or input("Path to voice sample (wav/m4a): ").strip()).strip()

    if not name:
        print("ERROR: Name is empty. Use --name \"Samuel\"")
        return

    if not audio:
        print("ERROR: Audio path is empty. Use --audio \"samples/samuel_register.m4a\"")
        return

    if not Path(audio).exists():
        print(f"ERROR: File not found -> {audio}")
        return

    register_student(name, audio)
    print(f"Registered voice for: {name}")

if __name__ == "__main__":
    main()
