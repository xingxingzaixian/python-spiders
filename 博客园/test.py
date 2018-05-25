# -*- coding: utf-8 -*-
from PIL import Image

def can_add(step, x, y):
    if step:
        if step[0] + 55 > x > step[0] - 10 and step[1] + 55 > y > step[1] - 10:
            return True
    return False

# 进一步处理灰度后的图片，将颜色相同的地方设置为白色，生成一个新的图片
def print_piexl(image_file, full_image):
    im = Image.open(image_file)
    full = Image.open(full_image)
    new_im = Image.new("RGB", im.size)
    for x in range(im.width):
        for y in range(im.height):
            cpx = im.getpixel((x, y))
            fpx = full.getpixel((x, y))
            if abs(cpx - fpx) > 50:
                new_im.putpixel((x,y), (cpx, 0, 0))
            else:
                new_im.putpixel((x, y), (255,255,255))

    new_im.save('3.png')

def huidu(cut_image, full_image):
    im = Image.open(cut_image)
    im = im.convert("L")
    im.save("cut.png")

    im = Image.open(full_image)
    im = im.convert("L")
    im.save("full.png")

def calc_offset():
    first = None
    first_total = 0
    second = None
    second_total = 0
    im = Image.open("3.png")
    for x in range(im.width):
        for y in range(im.height):
            px = im.getpixel((x, y))
            if px[0] != 255:
                if not first:
                    first = (x, y)

                if can_add(first, x, y):
                    first_total += px[0]
                else:
                    if first and not second:
                        second = (x, y)

                    if can_add(second, x, y):
                        second_total += px[0]

            if first and can_add(first, x, y):
                first_total += px[0]
            elif second and can_add(second, x, y):
                second_total += px[0]

    if first_total < second_total:
        print(first_total, second_total)

    with open("1.txt", "a") as fp:
        fp.write("{}\t{}\n".format(first_total, second_total))

if __name__ == "__main__":
    pass