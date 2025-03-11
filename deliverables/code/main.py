import subprocess
import shutil


# to keep things more modular
def run_command(command):
    try:
        print(f"Running: {' '.join(command)}")
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {' '.join(command)}: {e}")
        exit(1)

def main():

    # figure out which python command
    python_cmd = "python3" if shutil.which("python3") else "python"
    
    commands = [
        [python_cmd, "utils/finder.py"],
        [python_cmd, "modules/chunker.py"],
        [python_cmd, "modules/db.py"],
        [python_cmd, "modules/essay.py"]
    ]
    
    for cmd in commands:
        run_command(cmd)


if __name__ == "__main__":
    main()