import json
import argparse
from PIL import Image
from pathlib import Path
from os import makedirs
from BinPacker.BinPacker import BinPacker
from os import chdir
from tempfile import TemporaryDirectory
import numpy as np
import pyopencl as cl
import time

def positive_value(x) -> int:
    x = int(x)
    if x <= 0:
        raise argparse.ArgumentTypeError('Value must be a positive number')
    return x


argParser = argparse.ArgumentParser("Generate spritesheet")
argParser.add_argument('format', nargs='?', default='png', type=str,
                       help="Format of files from which spritesheet will be \
                            generated")
argParser.add_argument('-p', '--padding', nargs='?', default=5,
                       type=positive_value, help="Padding added to each image")
argParser.add_argument('-b', '--border', nargs='?', default=0,
                       type=positive_value, help="Border for each spritesheet")
argParser.add_argument('-mw', '--max-width', default=2048, type=positive_value,
                       help="Max width of spritesheet")
argParser.add_argument('-mh', '--max-height', default=2048,
                       type=positive_value, help="Max heigth of spritesheet")
argParser.add_argument('-d', '--dir', default='./',
                       type=str, help="Location where images are kept")
argParser.add_argument('-o', '--outfolder', default='out',
                       type=str, help="Name of output folder")
argParser.add_argument('-f', '--outFormat', default='png',
                       type=str, help="Format used to export spritesheets")


def processImage(image):
    k = image.load()
    for x in range(image.width):
        for y in range(image.height):
            try:
                if k[x, y][3] == 0:
                    k[x, y] = (0, 0, 0, 0)
            except TypeError:
                pass
    return (image.size, image.getbbox(), image.crop(image.getbbox()))


src = '''const sampler_t sampler = CLK_NORMALIZED_COORDS_FALSE | CLK_FILTER_NEAREST | CLK_ADDRESS_CLAMP_TO_EDGE;

__kernel void clearTransparency(__read_only image2d_t in, __write_only image2d_t out) {
    int2 coords = (int2)(get_global_id(0), get_global_id(1));

    uint4 pxVal = read_imageui(in, sampler, coords);
    
    if (pxVal.w == 0) {
        write_imageui(out, coords, (uint4)(0));
    } else {
        write_imageui(out, coords, pxVal);
    }
}'''


def cleanImages(files, tempPath):
    outData = {}

    plat = cl.get_platforms()
    GPU = plat[0].get_devices()
    ctx = cl.Context(GPU)
    queue = cl.CommandQueue(ctx)
    mf = cl.mem_flags
    # ustawienia formatu pliku
    ift = cl.ImageFormat(cl.channel_order.RGBA, cl.channel_type.UNSIGNED_INT8)
    prg = cl.Program(ctx, src).build()

    print("Start:", time.time())
    for file in files:
        name = Path(file).stem
        image = Image.open(file).convert("RGBA")
        shape = image.size

        imageIn = np.array(image)
        imageOut = np.empty_like(imageIn)
        imgInBuf = cl.image_from_array(ctx, imageIn, 4)
        imgOutBuf = cl.Image(ctx, mf.WRITE_ONLY, ift, shape=shape)
        prg.clearTransparency(queue, shape, None, imgInBuf, imgOutBuf)

        cl.enqueue_copy(
            queue,
            imageOut,
            imgOutBuf,
            origin=(0, 0),
            region=shape
        )

        path = Path(tempPath, f'{name}.npy')
        img = Image.fromarray(imageOut)
        padding = img.getbbox()
        img = img.crop(img.getbbox())
        newSize = img.size
        np.save(path, img)

        del imageIn
        del imageOut
        del imgInBuf
        del imgOutBuf
        del img
        image.close()
        outData[name] = {
            'path': path,
            'width': shape[0],
            'height': shape[1],
            '_width': newSize[0],
            '_height': newSize[1],
            'padding': padding
        }

    print("End:", time.time())
    return outData


def main() -> None:
    args = argParser.parse_args()

    # print(args.dir, args.format)
    chdir(Path(args.dir).resolve())
    files = list(Path('./').glob(f'*.{args.format}'))
    # print(files)
    # files = glob(f'*.{args.format}')

    if not len(files):
        return

    tempDir = TemporaryDirectory()

    # images = {Path(i).stem: processImage(Image.open(i)) for i in files}
    images = cleanImages(files, tempDir.name)

    sizes = [
        {
            'width': images[i]['_width'],
            'height': images[i]['_height'],
            'data': {
                'name': i
            }
        } for i in images
    ]

    packer = BinPacker(
        abs(args.max_width),
        abs(args.max_height),
        abs(args.padding),
        {
            'border:': abs(args.border)
        }
    )

    out = 0
    data = packer.addList(sizes).getData()
    outFolder = Path(args.outfolder)
    if not outFolder.exists():
        makedirs(outFolder)

    with open(outFolder / 'spritesheet.json', 'w', encoding='utf-8') as file:
        # spritesheet = [{**i['rects']} for i in data.copy()]
        spritesheet = {}
        for i in range(len(data)):
            t = {}
            for j in data[i]['rects'].keys():
                t[j] = {}
                t[j]['x'], t[j]['y'] = data[i]['rects'][j]['pos']
                t[j]['width'], t[j]['height'] = data[i]['rects'][j]['size']
                t[j]['pad_x'], t[j]['pad_y'], *_ = images[j]['padding']
            spritesheet[f'{out}.png'] = t.copy()
            out += 1

        json.dump(spritesheet, file, indent=4)

    out = 0

    for i in data:
        image = Image.new('RGBA', i['size'])

        for j in i['rects'].keys():
            image.paste(Image.fromarray(
                np.load(images[j]['path'])), i['rects'][j]['pos'])

        if args.outFormat == 'webp':
            image.save(str(outFolder / f'{out}.webp'),
                       lossless=True, quality=100, method=6)
        else:
            image.save(str(outFolder / f'{out}.{args.outFormat}'))
        out += 1


if __name__ == "__main__":
    main()
