from pathlib import Path

from daemoniker import Daemonizer
from daemoniker.exceptions import DaemonikerException

import reddit_bot

with Daemonizer() as (is_setup, daemonizer):
    if is_setup:
        # This code is run before daemonization.
        pid_file = Path(__file__).parent / 'f1_bot.pid'
        path_pid = str(pid_file)

    # We need to explicitly pass resources to the daemon; other variables
    # may not be correct
    is_parent = daemonizer(path_pid)

    if is_parent:
        # Run code in the parent after daemonization
        print("The process was forked to the background")

# We are now daemonized, and the parent just exited.
try:
    reddit_bot.main()
except DaemonikerException:
    pid_file.unlink()
