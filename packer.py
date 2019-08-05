import json
import argparse
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


def processImage(image):
    transparent = False
    k = image.load()
    for x in range(image.width):
        for y in range(image.height):
            if k[x, y][3] == 0:
                transparent = True
                k[x, y] = (0, 0, 0, 0)
    return (image.size, image.getbbox(), transparent, image.crop(image.getbbox()))


def main() -> None:
    args = argParser.parse_args()

    files = list(Path(args.dir).glob(f'*.{args.format}'))
    # files = glob(f'*.{args.format}')

    if not len(files):
        return 0

    images = {Path(i).stem: processImage(Image.open(i)) for i in files}

    sizes = [
        {
            'width': images[i][3].width,
            'height': images[i][3].height,
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
                t[j]['pad_x'], t[j]['pad_y'], *_ = images[j][1]
                t[j]['transparent'] = images[j][2]
            spritesheet[f'{out}.png'] = t.copy()
            out += 1

        json.dump(spritesheet, file, indent=4)

    out = 0

    for i in data:
        image = Image.new('RGBA', i['size'])

        for j in i['rects'].keys():
            image.paste(images[j][3], i['rects'][j]['pos'])

        image.save(str(outFolder / f'{out}.png'))
        out += 1


if __name__ == "__main__":
    main()
