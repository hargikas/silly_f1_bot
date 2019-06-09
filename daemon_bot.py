import io
from pathlib import Path

import psutil
from daemoniker import Daemonizer

import reddit_bot


def isDaemonRunning(pid_file):
    result = False
    if pid_file.exists():
        with io.open(str(pid_file), 'r', encoding='ascii') as f_obj:
            pid = int(f_obj.read().strip())
        if psutil.pid_exists(pid):
            p = psutil.Process(pid=pid)
            with p.oneshot():
                name = p.name()
            if name.lower() != 'python':
                pid_file.unlink()
            else:
                result = True
        else:
            pid_file.unlink()
    return result


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
reddit_bot.main()
