from .Bin import MaxBin
from .OversizedElementBin import OversizedBin
from .Rectangle import Rectangle
from random import randint

EDGE_MAX_VALUE = 4096
EDGE_MIN_VALUE = 64


class BinPacker():
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
            'tag': False,
            'border': 0
        }
        self.bins = []

        if type(options) == dict:
            self.options.update(options)

    @property
    def dirty(self):
        for bin in self.bins:
            if bin.dirty:
                return True
        return False

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
            for bin in self.bins:
                if type(bin) == OversizedBin:
                    continue
                added = bin.add(rect)
                if added:
                    break

            if not added:
                bin = MaxBin(
                    self.width, self.height, self.padding, self.options
                )

                if self.options['tag'] and rect.tag:
                    bin.tag = rect.tag

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
            rects = [
                Rectangle(i['width'], i['height'],
                          data=i.get('data', None)) for i in rects
                ]

        for i in self.sort(rects):
            self.add(i)

        return self

    def repack(self):
        if not self.dirty:
            return

        allRects = self.rects
        self.bins.clear()
        self.addList(allRects)

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
