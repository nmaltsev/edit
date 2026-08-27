import os

class ViewBox:
    def __init__(self, x, y, w, h):
        self.set(x, y, w, h)
        self.resize()

    def set(self, x, y, w, h):
        self._x = x
        self._y = y
        self._w = w
        self._h = h

    def resize(self, default=(80, 24)):
        try:
            self.terminal_size = os.get_terminal_size()
        except OSError:
            self.terminal_size = os.terminal_size(default)

    def x(self):
        if 0 < self._x < 1.0:
            return int(self._x * self.terminal_size.columns)
        return self._x

    def y(self):
        if 0 < self._y < 1.0:
            return int(self._y * self.terminal_size.lines)
        return self._y

    def w(self):
        if self._w is None:
            return int(self.terminal_size.columns - self.x())
        if 0 < self._w < 1.0:
            return int(self._w * self.terminal_size.columns)
        return self._w

    def h(self):
        if self._h is None:
            return int(self.terminal_size.lines - self.y())
        if 0 < self._h < 1.0:
            return int(self._h * self.terminal_size.lines)
        return self._h
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            values = (self.x(), self.y(), self.w(), self.h())
            return values[index]

        if index == 0:
            return self.x()
        elif index == 1:
            return self.y()
        elif index == 2:
            return self.w()
        elif index == 3:
            return self.h()

        raise IndexError("ViewBox index out of range")