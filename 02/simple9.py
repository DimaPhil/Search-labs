import numpy as np
from compressor import Compressor


class Simple9(Compressor):
    bws = [1, 2, 3, 4, 5, 7, 9, 14, 28]

    def __init__(self, elements=None):
        Compressor.__init__(self)
        self.elements = [] if elements is None else elements
        self.buf = []
        self.array = np.array(elements) if elements is not None else np.zeros((0,), dtype=np.int32)

    def iterate(self):
        self._commit_buf()
        for els in self.elements:
            for element in self._decode_group(els):
                yield element

    def __iter__(self):
        for e in self.array:
            yield e

    @staticmethod
    def _get_bit(x, b):
        return 1 if (x & (1 << b)) > 0 else 0

    def _decode_group_count(self, group):
        bit = (self._get_bit(group, 0) +
               self._get_bit(group, 1) * 2 +
               self._get_bit(group, 2) * 4 +
               self._get_bit(group, 3) * 8)
        return self._len_from_bit(bit)

    def _decode_group(self, group):
        n = self._decode_group_count(group)
        b = 4
        while b + n <= 32:
            e = 0
            p = 1
            for i in xrange(b, b + n):
                e += self._get_bit(group, i) * p
                p <<= 1
            yield e
            b += n

    @staticmethod
    def _bit_from_len(length):
        for i, l in enumerate(Simple9.bws):
            if length <= l:
                return i

    @staticmethod
    def _len_from_bit(bit):
        return Simple9.bws[bit]

    @staticmethod
    def _int_len(x):
        return int(np.ceil(np.log2(max(1, x))))

    def _commit_buf(self):
        if not self.buf:
            return
        bits = 28 / len(self.buf)
        result = self._bit_from_len(bits)
        els = 0
        p = 0
        for e in self.buf:
            els |= e << p
            p += bits
        result += els << 4
        self.buf = []
        self.elements.append(result)

    def _can_commit(self, x):
        if not self.buf:
            return True
        c = max(self._int_len(i) for i in self.buf)
        c = max(c, self._int_len(x))
        c = self._len_from_bit(self._bit_from_len(c))
        return c * (len(self.buf) + 1) <= 28

    def append(self, x):
        #if not self._can_commit(x):
        #    self._commit_buf()
        #self.buf.append(x)
        self.array = np.concatenate([self.array, np.array([x], dtype=np.int32)])

def iterate(elements):
    s = Simple9(elements)
    return s.__iter__()
'''
import numpy as np
from compressor import Compressor


class Simple9(Compressor):
    lens = [1, 2, 3, 4, 5, 7, 9, 14, 28]

    def __init__(self, elements=None):
        Compressor.__init__(self)
        if elements is None:
            self.array = np.zeros((0,), dtype=np.int32)
        else:
            self.array = np.array(elements)
        self.buf = []

    def __iter__(self):
        for element in self.array:
            yield element

    @staticmethod
    def _bit_from_len(length):
        for i, l in enumerate(Simple9.lens):
            if length <= l:
                return i

    @staticmethod
    def _len_from_bit(bit):
        lens = [1, 2, 3, 4, 5, 7, 9, 14, 28]
        return lens[bit]

    @staticmethod
    def _int_len(x):
        if x <= 1:
            return 1
        return int(np.ceil(np.log2(max(1, x - 1)))) + 1

    def _commit_buf(self):
        c = 28 / len(self.buf)
        c = self._bit_from_len(c)
        assert self._int_len(c) <= 4
        result = c << 28
        c = self._len_from_bit(c)
        print c, len(self.buf), c * len(self.buf)
        assert 28 - c < c * len(self.buf) <= 28
        k = 0
        for i in self.buf:
            result |= i << k
            k += c
        self.buf = []
        self.array = np.concatenate([self.array, np.array([result], dtype=np.int32)])

    def _buf_from_can(self, x):
        c = max(*(self._int_len(i) for i in self.buf + [x]))
        c = self._len_from_bit(self._bit_from_len(c))
        if c * (len(self.buf) + 1) <= 28:
            return True
        return False

    def append(self, x):
        self.array = np.concatenate([self.array, np.array([x], dtype=np.int32)])
'''