import numpy as np
from compressor import Compressor


class VarByteList(Compressor):
    def __init__(self, elements=None):
        Compressor.__init__(self)
        if elements is None:
            self.array = np.zeros((0,), dtype=np.int8)
        else:
            self.array = np.array(elements)

    def __iter__(self):
        cur_element = 0
        pos = 0
        start = True
        for element in self.array:
            if bool(element & (1 << 7)):
                cur_element |= (element ^ (1 << 7)) << pos
                yield cur_element
                pos = 0
                start = True
                cur_element = 0
            else:
                cur_element |= (element << pos)
                pos += 7
                start = False
        assert start

    def append(self, x):
        arr = []
        while x > 0:
            cur = np.int8(x & ((1 << 7) - 1))
            arr.append(cur)
            x >>= 7
        arr.append(np.int8(1 << 7))
        self.array = np.concatenate([self.array, np.uint8(arr)])


class VarByte(VarByteList):
    def __init__(self, elements=None):
        VarByteList.__init__(self, elements)
        self.last = 0

    def append(self, x):
        assert x >= self.last
        VarByteList.append(self, x - self.last)
        self.last = x

    def __iter__(self):
        cur = 0
        for i in VarByteList.__iter__(self):
            cur = cur + i
            yield cur


def iterate(elements):
    vb = VarByte(elements)
    return vb.__iter__()