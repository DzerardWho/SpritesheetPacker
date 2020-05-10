import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Dict

import lxml.etree as et
import numpy as np
from PIL import Image

from BinPacker.BinPacker import BinPacker


def positive_value(x) -> int:
    x = int(x)
    if x <= 0:
        raise argparse.ArgumentTypeError('Value must be a positive number')
    return x


homePath = Path('./')

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
        imageFile = Image.open(file).convert('RGBA')
        r, g, b, a = imageFile.split()
        shape = imageFile.size
        imageFile.close()

        mask = np.array(a) == 0
        r = Image.fromarray(
            np.ma.array(r, mask=mask).filled(0),
            'L'
        )
        g = Image.fromarray(
            np.ma.array(g, mask=mask).filled(0),
            'L'
        )
        b = Image.fromarray(
            np.ma.array(b, mask=mask).filled(0),
            'L'
        )

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


def getName(name: str, repNames: Dict[str, str]) -> str:
    if repNames is None or name not in repNames:
        return name
    return repNames[name]


def toJson(
        data: list,
        images,
        outFolder: Path,
        outFormat: str,
        repNames: Dict[str, str]
) -> None:
    out = 0
    spritesheet = {}
    for i in range(len(data)):
        t = {}
        for j in data[i]['rects'].keys():
            name = getName(j, repNames)
            t[name] = {}
            t[name]['x'], t[j]['y'] = data[i]['rects'][j]['pos']
            t[name]['width'], t[j]['height'] = data[i]['rects'][j]['size']
            t[name]['pad_x'], t[j]['pad_y'], *_ = images[j]['padding']
        spritesheet[f'{out}.{outFormat}'] = t.copy()
        out += 1

    (outFolder / 'spritesheet.json').write_text(
        json.dumps(spritesheet, indent=4)
    )


def toXml(
        data: list,
        images,
        outFolder: Path,
        outFormat: str,
        repNames: Dict[str, str]
) -> None:
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
            attribs['n'] = getName(j, repNames)
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


def main(args: argparse.Namespace, repNames: Dict[str, str] = None) -> None:
    # chdir(Path(args.dir).resolve())
    global homePath
    homePath = Path(args.dir).resolve()
    files = list(homePath.glob(f'*.{args.format}'))

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
        outFolder.mkdir(parents=True)

    if args.xml:
        toXml(data, images, outFolder, args.outFormat, repNames)
    else:
        toJson(data, images, outFolder, args.outFormat, repNames)

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


def run():
    main(argParser.parse_args())


if __name__ == "__main__":
    run()
