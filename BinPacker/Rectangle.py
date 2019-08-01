class Rectangle:
    _x = 0
    _y = 0
    _width = 0
    _height = 0
    _rot = False
    _data = {}
    _dirty = 0
    oversized = False

    def __init__(self, width=0, height=0, x=0, y=0, rot=False, data=None):
        """rot => rotated"""
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.rot = rot
        self._dirty = 0
        self.tag = None
        self.data = data

    def collide(self, r):
        return (r.x < self.x + self.width and
                r.x + r.width > self.x and
                r.y < self.y + self.height and
                r.y + r.height > self.y)

    def contain(self, r):
        return (r.x >= self.x and
                r.y >= self.y and
                r.x + r.width <= self.x + self.width and
                r.y + r.height <= self.y + self.height)

    def area(self):
        return self.width * self.height

    @property
    def dirty(self):
        return self._dirty > 0

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, val):
        if val == self._width:
            return
        self._width = val
        self._dirty += 1

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, val):
        if val == self._height:
            return
        self._height = val
        self._dirty += 1

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        if val == self._x:
            return
        self._x = val
        self._dirty += 1

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        if val == self._y:
            return
        self._y = val
        self._dirty += 1

    @property
    def rot(self):
        return self._rot

    @rot.setter
    def rot(self, val):
        if self._rot != val:
            self._width, self._height = self._height, self._width
            self._rot = val
            self._dirty += 1

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, val):
        if val == self._data:
            return
        self._data = val
        self._dirty += 1

    def setDirty(self, value):
        self._dirty = self._dirty + 1 if value else 0

    def __lt__(self, val):
        r = max(val.width, val.height) - max(self.width, self.height)
        if r == 0:
            return min(val.width, val.height) - min(self.width, self.height) < 0
        return r > 0

    def getData(self):
        return {
            'width': self.width,
            'height': self.height,
            'data': self.data,
            'x': self.x,
            'y': self.y,
        }