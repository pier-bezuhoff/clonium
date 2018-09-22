import json
import os.path as op
from operator import getitem
from functools import reduce

from panda3d.core import Vec3, VBase4

settings_filename = "settings.json"
outer_folder = op.split(__file__)[0]
filename = op.join(outer_folder, settings_filename)
with open(filename) as file:
    tree = json.loads(file.read())


def request(s):
    """s :== '<name1>.<name2>.....<nameN>'
    response = tree['<name1>']['<name2>']...['<nameN>']"""
    return reduce(getitem, s.split('.'), tree)


def request_vector(s):
    return Vec3(*request(s))


def request_color(s):
    return VBase4(*request(s))


def request_colors(s):
    return [VBase4(*coors) for coors in request(s)]
