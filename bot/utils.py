import subprocess
from config import SCRIPTS_DIR

def run_script(name):
    path = f"{SCRIPTS_DIR}/{name}"
    try:
        output = subprocess.check_output(["bash", path], stderr=subprocess.STDOUT)
        return output.decode()
    except subprocess.CalledProcessError as e:
        return e.output.decode()
