import json
import argparse
from glob import glob
from PIL import Image
from pathlib import Path
from os import makedirs
from BinPacker.BinPacker import BinPacker


def positive_value(x) -> int:
    x = int(x)
    if x <= 0:
        raise argparse.ArgumentTypeError('Value must be a positive number')
    return x


argParser = argparse.ArgumentParser("Generate spritesheet")
argParser.add_argument('format', nargs='?', default='./*.png', type=str,
                       help="Format of files from which spritesheet will be generated")
argParser.add_argument('-p', '--padding', nargs='?', default=5,
                       type=positive_value, help="Padding added to each image")
argParser.add_argument('-b', '--border', nargs='?', default=0,
                       type=positive_value, help="Border for each spritesheet")
argParser.add_argument('-mw', '--max-width', default=2048, type=positive_value,
                       help="Max width of spritesheet")
argParser.add_argument('-mh', '--max-height', default=2048,
                       type=positive_value, help="Max heigth of spritesheet")
argParser.add_argument('-o', '--outfolder', default='out',
                       type=str, help="Name of output folder")


def main() -> None:
    args = argParser.parse_args()

    files = glob(f'*.{argParser.format}')

    if not len(files):
        return 0

    images = {Path(i).stem: Image.open(i) for i in files}

    sizes = [
        {
            'width': images[i].width,
            'height': images[i].height,
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
        spritesheet = []
        for i in range(len(data)):
            t = {}
            for j in data[i]['rects'].keys():
                t[j] = {}
                t[j]['x'], t[j]['y'] = data[i]['rects'][j]['pos']
                t[j]['width'], t[j]['height'] = data[i]['rects'][j]['size']
            spritesheet.append(t)

        json.dump(spritesheet, file, indent=4)

    for i in data:
        image = Image.new('RGBA', i['size'])

        for j in i['rects'].keys():
            image.paste(images[j], i['rects'][j]['pos'])

        image.save(str(outFolder / f'{out}.png'))
        out += 1


if __name__ == "__main__":
    main()
