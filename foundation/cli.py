#!/usr/bin/env python

import logging
import clize
from collegium.foundation.jupyter_render import jupyter_process


def hello():
    print("world")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    clize.run([hello, jupyter_process])
