import os
import sys

# Redirect stderr within the Python script
# devnull = os.open(os.devnull, os.O_WRONLY)
# old_stderr = os.dup(2)
# sys.stderr.flush()
# os.dup2(devnull, 2)
# os.close(devnull)

from src.TravelApp import App

if __name__ == '__main__':
    App(test_mode=False, ring_mouse_mode=True)
