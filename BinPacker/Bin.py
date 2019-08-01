from .Rectangle import Rectangle
from .AbstractBin import Bin
import sys
import math


class MaxBin(Bin):
    def __init__(self, maxWidth, maxHeight, padding=0, options=None):
        super().__init__()

        if type(options) == dict:
            self.options.update(options)

        self.padding = padding
        self.width = 0 if self.options['smart'] else maxWidth
        self.height = 0 if self.options['smart'] else maxHeight
        self.maxWidth = maxWidth
        self.maxHeight = maxHeight
        self.border = self.options['border']
        self.freeRects.append(Rectangle(
            self.maxWidth + self.padding - self.border * 2,
            self.maxHeight + self.padding - self.border * 2,
            self.border,
            self.border
        ))

        self.stage = Rectangle(self.width, self.height)
        self.verticalExpand = self.width > self.height

    def repack(self):
        unpacked = []
        self.rects.sort(reverse=True)

        for i in self.rects:
            if not self.place(i):
                unpacked.append(i)

        self.reset()

    def findNode(self, width, height):
        score = sys.maxsize
        bestNode = None
        for i in self.freeRects:
            if i.width >= width and i.height >= height:
                areaFit = i.area() - width * height
                if areaFit < score:
                    bestNode = Rectangle(width, height, i.x, i.y)
                    score = areaFit

        return bestNode

    def expandFreeRects(self, width, height):
        for i in range(len(self.freeRects)):
            if self.freeRects[i].x + self.freeRects[i].width \
                    >= min(self.width + self.padding - self.border, width):
                self.freeRects[i].width = width - \
                    self.freeRects[i].x - self.border

            if self.freeRects[i].y + self.freeRects[i].height \
                    >= min(self.height + self.padding - self.border, height):
                self.freeRects[i].height = height - \
                    self.freeRects[i].y - self.border

        self.freeRects.append(Rectangle(
            width - self.width - self.padding,
            height - self.border * 2,
            self.width + self.padding - self.border,
            self.border
        ))
        self.freeRects.append(Rectangle(
            width - self.border * 2,
            height - self.height - self.padding,
            self.border,
            self.height + self.padding - self.border
        ))
        self.freeRects = list(filter(lambda x: not(
            x.width <= 0 or x.height <= 0 or
            x.x < self.border or x.y < self.border
        ), self.freeRects))
        self.pruneFreeList()

    def updateBinSize(self, node):
        if not self.options['smart'] or self.stage.contain(node):
            return False
        tmpWidth = max(self.width, node.x + node.width -
                       self.padding + self.border)
        tmpHeight = max(self.height, node.y + node.height -
                        self.padding + self.border)

        if self.options['pot']:
            tmpWidth = 2 ** math.ceil(math.log2(tmpWidth))
            tmpHeight = 2 ** math.ceil(math.log2(tmpHeight))

        if self.options['square']:
            tmpWidth = tmpHeight = max(tmpWidth, tmpHeight)

        if tmpWidth > self.maxWidth + self.padding or \
                tmpHeight > self.maxHeight + self.padding:
            return False

        self.expandFreeRects(tmpWidth + self.padding, tmpHeight + self.padding)
        self.width = self.stage.width = tmpWidth
        self.height = self.stage.height = tmpHeight
        return True

    def splitNode(self, freeRect, usedNode):
        if not freeRect.collide(usedNode):
            return False

        # Vertical split
        if usedNode.x < freeRect.x + freeRect.width and \
                usedNode.x + usedNode.width > freeRect.x:
            # New node at the top side of the used node
            if usedNode.y > freeRect.y and \
                    usedNode.y < freeRect.y + freeRect.height:
                self.freeRects.append(Rectangle(
                    freeRect.width,
                    usedNode.y - freeRect.y,
                    freeRect.x,
                    freeRect.y
                ))

            # New node at the bottom of the used node
            if usedNode.y + usedNode.height < freeRect.y + freeRect.height:
                self.freeRects.append(Rectangle(
                    freeRect.width,
                    freeRect.y + freeRect.height -
                    (usedNode.y + usedNode.height),
                    freeRect.x,
                    usedNode.y + usedNode.height
                ))

        # Horizontal split
        if usedNode.y < freeRect.y + freeRect.height and \
                usedNode.y + usedNode.height > freeRect.y:
            # New node at the left side of the used node
            if usedNode.x > freeRect.x and \
                    usedNode.x < freeRect.x + freeRect.width:
                self.freeRects.append(Rectangle(
                    usedNode.x - freeRect.x,
                    freeRect.height,
                    freeRect.x,
                    freeRect.y
                ))

            # New node at the right of the used node
            if usedNode.x + usedNode.width < freeRect.x + freeRect.width:
                self.freeRects.append(Rectangle(
                    freeRect.x + freeRect.width -
                    (usedNode.x + usedNode.width),
                    freeRect.height,
                    usedNode.x + usedNode.width,
                    freeRect.y
                ))

        return True

    def pruneFreeList(self):
        i, j = 0, 0
        lenR = len(self.freeRects)
        while (i < lenR):
            j = i + 1
            tmpRect1 = self.freeRects[i]
            while (j < lenR):
                tmpRect2 = self.freeRects[j]
                if tmpRect2.contain(tmpRect1):
                    self.freeRects.remove(tmpRect1)
                    i -= 1
                    lenR -= 1
                    break

                if tmpRect1.contain(tmpRect2):
                    self.freeRects.remove(tmpRect2)
                    j -= 1
                    lenR -= 1

                j += 1
            i += 1

    def place(self, rect):
        if self.options['tag'] and self.tag != rect.tag:
            return False

        node = self.findNode(
            rect.width + self.padding, rect.height + self.padding
        )

        if node:
            self.updateBinSize(node)
            numRectToProcess = len(self.freeRects)
            i = 0

            while(i < numRectToProcess):
                if self.splitNode(self.freeRects[i], node):
                    del self.freeRects[i]
                    i -= 1
                i += 1

            self.pruneFreeList()
            self.verticalExpand = self.width > self.height
            rect.x = node.x
            rect.y = node.y
            self._dirty += 1

            return rect

        elif not self.verticalExpand:
            if self.updateBinSize(Rectangle(
                rect.width + self.padding,
                rect.height + self.padding,
                self.width + self.padding - self.border,
                self.border
            )) or self.updateBinSize(Rectangle(
                    rect.width + self.padding,
                    rect.height + self.padding,
                    self.border,
                    self.height + self.padding - self.border
            )):
                return self.place(rect)
        else:
            if self.updateBinSize(Rectangle(
                rect.width + self.padding,
                rect.height + self.padding,
                self.border,
                self.height + self.padding - self.border
            )) or self.updateBinSize(Rectangle(
                    rect.width + self.padding,
                    rect.height + self.padding,
                    self.width + self.padding - self.border,
                    self.border
            )):
                return self.place(rect)

        return False

    def reset(self):
        if self.data:
            self.data.clear()
        if self.tag:
            self.tag = None
        self.rects.clear()

        self.width = 0 if self.options['smart'] else self.maxWidth
        self.height = 0 if self.options['smart'] else self.maxHeight
        self.border = self.options['border']
        self.freeRects.clear()
        self.freeRects.append(Rectangle(
            self.maxWidth + self.padding - self.border * 2,
            self.maxHeight + self.padding - self.border * 2,
            self.border,
            self.border
        ))
        self.stage = Rectangle(self.width, self.height)
        self._dirty = 0

    def add(self, rect=None, width=None, height=None, data=None):
        if rect:
            if self.options['tag'] and self.tag != rect.tag:
                return False
        elif width and height:
            if self.options['tag']:
                if data and 'tag' in data and self.tag != data['tag']:
                    return False
                if not data and self.tag:
                    return False

            rect = Rectangle(width, height)
            rect.data = data
            rect.setDirty(False)

        result = self.place(rect)
        if result:
            self.rects.append(rect)
        return result
