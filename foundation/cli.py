import clize
from foundation.jupyter_render import jupyter_process


def hello():
    print('world')


if __name__ == '__main__':
    clize.run([hello, jupyter_process])