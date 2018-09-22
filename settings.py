from preference import request, outer_folder


def folder(name, prefix="paths.", postfix="_folder"):
    return "{}/{}".format(outer_folder, request(prefix + name + postfix))

def theme(name=request("core.theme")):
    return "{}/{}".format(folder("theme"), name)

def clip_filename(n, color_i, set=request("paths.set_folder").format(image_lib=folder("image"), name=request("core.set"))):
    return request("paths.clip_filename").format(set=set, n=n, color_i=color_i)

def game_icon():
    return request("game.icon").format(image_lib=folder("image"))

def cell_brush_filename():
    return request("map_editor.cell_brush").format(image_lib=folder("image"))

def none_brush_filename():
    return request("map_editor.none_brush").format(image_lib=folder("image"))

def save_filename(name=request("paths.autosave_name")):
    return request("paths.filename").format(lib=folder("save"), name=name, ext=request("formats.save.extension"))

def map_filename(name):
    return request("paths.filename").format(lib=folder("map"), name=name, ext=request("formats.map.extension"))
