from pathlib import Path
import io

from daemoniker import Daemonizer
import psutil

import reddit_bot
import time

def isDaemonRunning(pid_file):
    if pid_file.exists():
        with io.open(pid_file, 'r', enconding='ascii') as f_obj:
            pid = int(f_obj.read().strip())
        if psutil.pid_exists(pid):
            p = psutil.Process(pid=pid)
            with p.oneshot():
                name = p.name()
                status = p.status()
            print("Found process:", name, status)

with Daemonizer() as (is_setup, daemonizer):
    if is_setup:
        # This code is run before daemonization.
        pid_file = Path(__file__).parent / 'f1_bot.pid'
        path_pid = str(pid_file)
        isDaemonRunning(pid_file)
        

    # We need to explicitly pass resources to the daemon; other variables
    # may not be correct
    is_parent = daemonizer(path_pid)

    if is_parent:
        # Run code in the parent after daemonization
        print("The process was forked to the background")

# We are now daemonized, and the parent just exited.
#reddit_bot.main()
time.sleep(300)