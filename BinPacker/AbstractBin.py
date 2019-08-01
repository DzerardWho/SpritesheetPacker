class Bin:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.maxWidth = 0
        self.maxHeight = 0
        self.freeRects = []
        self.rects = []
        self.options = {'smart': True, 'pot': True, 'square': True,
                        'allowRotation': False, 'tag': False, 'border': 0}
        self.data = None
        self.tag = None
        self._dirty = 0

    def add(self, rect=None, width=None, height=None, data=None):
        pass

    def reset(self, deepReset):
        pass

    def repack(self):
        pass

    @property
    def dirty(self):
        return self._dirty > 0 or any([i.dirty for i in self.rects])

    def setDirty(self, value=True):
        self._dirty = self._dirty + 1 if value else 0
        if not value:
            for i in self.rects:
                if hasattr(i, 'setDirty'):
                    i.setDirty(False)

    def __len__(self):
        return len(self.rects)