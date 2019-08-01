from .AbstractBin import Bin
from .Rectangle import Rectangle


class OversizedBin(Bin):
    def __init__(self, rect=None, width=None, height=None, data=None):
        super().__init__()
        if rect:
            self.width = rect.width
            self.height = rect.height
            self.data = rect.data
        elif width and height:
            self.width = width
            self.height = height
            self.data = data
            rect = Rectangle(width, height)
            rect.data = data

        rect.oversized = True
        self.rects.append(rect)
        self.maxWidth = self.width
        self.maxHeight = self.height
        self.options['smart'] = self.options['pot'] = \
            self.options['square'] = False

    def add(self, rect):
        return None

    def reset(self):
        pass

    def repack(self):
        return None
