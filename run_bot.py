import os
import time
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO,
                    filename="runner.log",
                    filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

PIDFILE = "bot.pid"

def is_running(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

if os.path.exists(PIDFILE):
    try:
        with open(PIDFILE, "r") as f:
            oldpid = int(f.read().strip())
        if not is_running(oldpid):
            os.remove(PIDFILE)
        else:
            logging.info(f"Process already running with PID {oldpid}. Exiting runner.")
            print("Bot already running. Exiting runner.")
            sys.exit(0)
    except Exception:
        try:
            os.remove(PIDFILE)
        except Exception:
            pass

while True:
    logging.info("Starting bot.py ...")
    p = subprocess.Popen([sys.executable, "bot.py"])
    logging.info(f"Started bot.py with PID {p.pid}")
    with open(PIDFILE, "w") as f:
        f.write(str(p.pid))
    p.wait()
    logging.info(f"bot.py exited with code {p.returncode} — restarting in 1s")
    try:
        if os.path.exists(PIDFILE):
            os.remove(PIDFILE)
    except Exception:
        pass
    time.sleep(1)
