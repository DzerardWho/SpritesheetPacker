from Bin import MaxBin
from OversizedElementBin import OversizedBin
from Rectangle import Rectangle
from random import randint

EDGE_MAX_VALUE = 4096
EDGE_MIN_VALUE = 64


class RectPacker():
    def __init__(
            self,
            width=EDGE_MAX_VALUE,
            height=EDGE_MAX_VALUE,
            padding=0,
            options=None
    ):
        self.width = width
        self.height = height
        self.padding = padding
        self.options = {
            'smart': True,
            'pot': True,
            'square': False,
            'allowRotation': False,
            'tag': False,
            'border': 0
        }
        self._currentBin = 0
        self.bins = []

        if type(options) == dict:
            self.options.update(options)

    @property
    def currentBin(self):
        return self._currentBin

    @property
    def dirty(self):
        return any([bin.dirty for bin in self.bins])

    @property
    def rects(self):
        allRects = []
        for bin in self.bins:
            allRects.extend(bin.rects)

        return allRects

    def add(self, rect=None, width=None, height=None, data=None):
        if rect:
            if type(rect) is not Rectangle:
                if not ('width' in rect or 'height' in rect):
                    raise Exception("Invalid argument 'rect'")

                data = rect.get('data', None)
                rect = Rectangle(rect['width'], rect['height'])
                rect.data = data
        elif width and height:
            rect = Rectangle(width, height)
            rect.data = data

        if rect.width > self.width or rect.height > self.height:
            self.bins.append(OversizedBin(rect))
        else:
            added = False
            for bin in self.bins[self._currentBin:]:
                if type(bin) == OversizedBin:
                    continue
                added = bin.add(rect)
                if added:
                    break

            if not added:
                bin = MaxBin(
                    self.width, self.height, self.padding, self.options
                )
                if 'tag' in rect.data:
                    tag = rect.data['tag']
                elif hasattr(rect, 'tag'):
                    tag = rect.tag
                else:
                    tag = None

                if self.options['tag'] and tag:
                    bin.tag = tag

                bin.add(rect)
                self.bins.append(bin)

        return rect

    def sort(self, rects):
        # if type(rects[0]) == dict:
        #     return sorted(rects, key=lambda x: max(x['width'], x['height']),
        #                   reverse=True)
        return sorted(rects, reverse=True)

    def addList(self, rects):
        if len(rects) and type(rects[0]) is not Rectangle:
            rects = [Rectangle(i['width'], i['height'], data=i.get('data', None)) for i in rects]

        for i in self.sort(rects):
            self.add(i)

    def reset(self):
        self.bins.clear()
        self._currentBin = 0

    def next(self):
        self._currentBin = len(self.bins)
        return self._currentBin

    def repack(self, quick=True):
        if quick:
            unpack = []
            for bin in self.bins:
                if bin.dirty:
                    up = bin.repack()
                    if up:
                        unpack.extend(up)
            self.addList(unpack)
            return

        if not self.dirty:
            return

        allRects = self.rects
        self.reset()
        self.addList(allRects)

    def save(self):
        saveBins = []
        for bin in self.bins:
            saveBin = {
                'width': bin.width,
                'height': bin.height,
                'maxWidth': bin.maxWidth,
                'maxHeight': bin.maxHeight,
                'freeRects': [
                    {
                        'x': i.x,
                        'y': i.y,
                        'width': i.width,
                        'height': i.height
                    } for i in bin.freeRects
                ],
                'rects': list(bin.rects),
                'options': bin.options
            }
            if bin.tag:
                saveBin['tag'] = bin.tag

            saveBins.append(saveBin)

        return saveBins

    def load(self, bins):
        index = 0
        for bin in bins:
            if bin.maxWidth > self.width or bin.maxHeight > self.height:
                self.bins.append(OversizedBin(None, bin['width'],
                                              bin['height']))
            else:
                newBin = MaxBin(self.width, self.height,
                                self.padding, bin['options'])

                newBin.freeRects.clear()
                for i in bin['freeRects']:
                    newBin.freeRects.append(Rectangle(
                        i['width'], i['height'], i['x'], i['y']
                    ))
                    newBin.width = bin.width
                    newBin.height = bin.height
                    if 'tag' in bin:
                        newBin.tag = bin['tag']
                    self.bins[index]
                    index += 1

    def getData(self):
        data = []
        for bin in self.bins:
            data.append({
                'size': (bin.width, bin.height),
                'rects': {
                    i.data.get('name', randint(0, 99999999999999)): {
                        'pos': (i.x, i.y),
                        'size': (i.width, i.height),
                        'data': i.data,
                    } for i in bin.rects
                }
            })
            if len(bin.rects) == 1:
                t = bin.rects[0]
                data[-1]['size'] = (t.width, t.height)
        return data
