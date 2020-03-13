import json
import argparse
import lxml.etree as et
from PIL import Image
from pathlib import Path
from os import makedirs
from BinPacker.BinPacker import BinPacker
from os import chdir
from tempfile import TemporaryDirectory
import numpy as np
from typing import List, Dict


def positive_value(x) -> int:
    x = int(x)
    if x <= 0:
        raise argparse.ArgumentTypeError('Value must be a positive number')
    return x


argParser = argparse.ArgumentParser("Generate spritesheet")
argParser.add_argument('format', nargs='?', default='png', type=str,
                       help="Format of files from which spritesheet will be "
                            "generated")
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
argParser.add_argument('-x', '--xml', default=False, action='store_true',
                       help="Export spritesheet as xml, json otherwise")


def cleanImages(files: List[Path], tempPath: Path) -> Dict[str, Dict]:
    outData = {}

    for file in files:
        name = Path(file).stem
        imageFile = Image.open(file)
        image = np.array(imageFile.convert("RGBA"))
        imageFile.close()
        shape = image.shape

        mask = image[:, :, 3] == 0
        r = Image.fromarray(
            np.ma.array(image[:, :, 0], mask=mask).filled(0),
            'L'
        )
        g = Image.fromarray(
            np.ma.array(image[:, :, 1], mask=mask).filled(0),
            'L'
        )
        b = Image.fromarray(
            np.ma.array(image[:, :, 2], mask=mask).filled(0),
            'L'
        )
        a = Image.fromarray(image[:, :, 3], 'L')

        path = Path(tempPath, f'{name}.npy')
        img = Image.merge('RGBA', [r, g, b, a])
        padding = img.getbbox()
        img = img.crop(img.getbbox())
        newSize = img.size
        np.save(path, img)

        del img
        outData[name] = {
            'path': path,
            'width': shape[0],
            'height': shape[1],
            '_width': newSize[0],
            '_height': newSize[1],
            'padding': padding
        }

    return outData


def toJson(data: list, images, outFolder: Path, outFormat: str) -> None:
    out = 0
    spritesheet = {}
    for i in range(len(data)):
        t = {}
        for j in data[i]['rects'].keys():
            t[j] = {}
            t[j]['x'], t[j]['y'] = data[i]['rects'][j]['pos']
            t[j]['width'], t[j]['height'] = data[i]['rects'][j]['size']
            t[j]['pad_x'], t[j]['pad_y'], *_ = images[j]['padding']
        spritesheet[f'{out}.{outFormat}'] = t.copy()
        out += 1

    (outFolder / 'spritesheet.json').write_text(
        json.dumps(spritesheet, indent=4)
    )


def toXml(data: list, images, outFolder: Path, outFormat: str) -> None:
    out = 0
    root = et.Element('spritesheets')
    for i in range(len(data)):
        sheet: et.Element = et.Element('sheet', attrib={
            'name': f'{out}.{outFormat}'
        })
        root.append(sheet)
        out += 1
        for j in data[i]['rects'].keys():
            attribs = {}
            attribs['n'] = j
            attribs['x'], attribs['y'] = data[i]['rects'][j]['pos']
            attribs['w'], attribs['h'] = data[i]['rects'][j]['size']
            attribs['px'], attribs['py'], *_ = images[j]['padding']

            elem = et.Element('img', attrib={
                k: str(v) for k, v in attribs.items()
            })
            sheet.append(elem)
    (outFolder / 'spritesheet.xml').write_bytes(
        et.tostring(root, pretty_print=True)
    )


def main(args: argparse.Namespace) -> None:
    chdir(Path(args.dir).resolve())
    files = list(Path('./').glob(f'*.{args.format}'))

    if not len(files):
        return

    tempDir = TemporaryDirectory()

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

    data = packer.addList(sizes).getData()
    outFolder = Path(args.outfolder)
    if not outFolder.exists():
        makedirs(outFolder)

    if args.xml:
        toXml(data, images, outFolder, args.outFormat)
    else:
        toJson(data, images, outFolder, args.outFormat)

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
    main(argParser.parse_args())
