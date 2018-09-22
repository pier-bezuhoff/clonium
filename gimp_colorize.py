INPUT_PATTERN = "{}/star-{}.png"
OUTPUT_PATTERN = "{}/item{}-{}.png"
OPACITY = 50
COLORS = [
    (0, 0, 0), (255, 128, 0), (255, 128, 128),
    (128, 0, 128), (0, 0, 128), (0, 128, 0),
    (128, 0, 0), (128, 64, 0), (64, 128, 255),
    (128, 128, 128), (255, 255, 255)]

def init(the_pdb, the_gimp):
    global pdb, gimp
    pdb = the_pdb
    gimp = the_gimp

def mult(image, colors, target_layer, n, folder, pattern=OUTPUT_PATTERN):
    for color in colors:
        pdb.gimp_context_set_foreground(color)
        target_layer.fill()
        new_image = pdb.gimp_image_duplicate(image)
        layer = pdb.gimp_image_merge_visible_layers(new_image, CLIP_TO_IMAGE)
        pdb.gimp_file_save(new_image, layer, pattern.format(folder, n, colors.index(color)), '?')
        pdb.gimp_image_delete(new_image)

def main():
    for i in range(1, 9):
        new_image = pdb.gimp_file_load(INPUT_PATTERN.format(folder, i), '?')
        target = gimp.Layer(new_image, 'target', new_image.width, new_image.height, RGB_IMAGE, OPACITY, NORMAL_MODE)
        new_image.add_layer(target)
        new_image.raise_layer(new_image.layers[-1])
        mult(new_image, COLORS, target, i, folder)
