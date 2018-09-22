#!/usr/bin/env python3
from PIL import Image
from itertools import product
import settings

def as_mask(color, image):
	pixels = image.load()
	flat = lambda: product(range(image.width), range(image.height))
	m = min(pixels[pos][0] for pos in flat())
	M = max(pixels[pos][0] for pos in flat())
	denominator = M - m
	for pos in flat():
		pixels[pos] = mult_color(color, pixels[pos], denominator)
	return image

def mult_color(c1, c2, denominator=255):
	return tuple([int(round(c1[i]*c2[0]/denominator)) for i in range(3)] + list(c2[3:]))

def colorize(color, path, out_path):
	as_mask(color, Image.open(path)).save(out_path)

def ask_colorize():
	path = input("Image path: ") or path
	print(path)
	out_path = input("Image save path: ") or out_path
	print(out_path)
	color = eval(input("Color ($1, $2, $3):\n")) or color
	print(color)
	colorize(color, path, out_path)

def main():
	path1 = "lib/images/item{}.png"
	path2 = "lib/images/second_set/item{}-{}.png"
	for i in range(1, 6):
		path = path1.format(i)
		for j, color in enumerate(settings.COLORS):
			out_path = path2.format(i, j)
			# print(color, path, out_path)
			colorize(color, path, out_path)

path = "lib/images/item4.png"
out_path = "lib/images/result4.png"
color = (255, 255, 0)

if __name__ == '__main__':
	main()
