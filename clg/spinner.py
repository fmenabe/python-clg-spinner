# coding: utf-8

"""Manage a terminal spinner.

The spinner has the same methods as `clg-logger` module. Levels of the message
have different behaviors:
    * *info* messages are printed in the spinner
    * *warn* and *error* messages are printed when the spinner has stopped
    * *verbose* and *debug* messages are printed as they come (and so, they
      break the spinner).
Except for the *info* level, the `clg-logger` is use by default for printing
the messages.
"""

import os
import sys
import time
import threading
import itertools
import subprocess
from contextlib import contextmanager
import clg.logger as logger

shell_width = lambda: int(subprocess.check_output(['tput', 'cols']))

class Spinner(threading.Thread):
    spinner = itertools.cycle(['-', '\\', '|', '/'])

    def __init__(self, event_hdl=logger):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self.event_hdl = event_hdl
        self.msg = None
        self.messages = []
        self.quit = False
        self.return_code = 0

    def run(self):
        while not self._stop_event.isSet():
            # Just wait for a message or a stop
            if self.msg is not None:
                sys.stdout.write("\x1b[2K\r%s %s" % (next(self.spinner), self.msg))
                sys.stdout.flush()
            self._stop_event.wait(0.2)
        sys.stdout.write("\x1b[2K\r")
        sys.stdout.flush()

        for message in self.messages:
            message()

        # Force exit of the program!
        if self.quit:
            os._exit(self.return_code)

    def stop(self):
        self._stop_event.set()
        self.msg = None
        sys.stdout.write("\x1b[2k\r")
        time.sleep(0.1)

    def log(self, msg, loglevel, **kwargs):
        self.quit = kwargs.pop('quit', False)
        self.return_code = kwargs.pop('return_code', 0)

        self.messages.append(lambda: getattr(self.event_hdl, loglevel)(msg, **kwargs))

        if self.quit:
            self.stop()

    def verbose(self, msg, **kwargs):
        getattr(self.event_hdl, 'verbose')(msg, **kwargs)

    def debug(self, msg, **kwargs):
        getattr(self.event_hdl, 'debug')(msg, **kwargs)

    def info(self, msg, **kwargs):
        self.msg = msg
        # Force message to be visible.
        time.sleep(0.1)

    def warn(self, msg, **kwargs):
        self.log(msg, 'warn', **kwargs)

    def error(self, msg, **kwargs):
        self.log(msg, 'error', return_code=kwargs.pop('return_code', 1), **kwargs)

@contextmanager
def start():
    try:
        spinner = Spinner()
        spinner.start()
        setattr(sys.modules[__name__], 'spinner', spinner)
        yield None
    except KeyboardInterrupt:
        sys.exit(1)
    finally:
        stop()

stop = lambda: spinner.stop()
verbose = lambda msg, **kwargs: spinner.verbose(msg, **kwargs)
debug = lambda msg, **kwargs: spinner.debug(msg, **kwargs)
info = lambda msg, **kwargs: spinner.info(msg, **kwargs)
warn = lambda msg, **kwargs: spinner.warn(msg, **kwargs)
error = lambda msg, **kwargs: spinner.error(msg, **kwargs)
