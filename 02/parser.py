import re
import json
from simple9 import iterate
import mmap
import os.path


SPLIT_RGX = re.compile(r'\w+|[\(\)&\|!]', re.UNICODE)
N = 10**6


def restore_bucket(data):
    m = {}
    data = data[1:len(data) - 2]
    for p in data.split(')'):
        w, v = p.split(',[')
        w = json.loads(w[1:])
        m[w] = json.loads('[' + v)
    return m


def restore(index_path, offsets, word):
    bucket = hash(word) % N
    begin = offsets[bucket]
    if bucket == N - 1:
        length = os.path.getsize(index_path) - begin
    else:
        length = offsets[bucket + 1] - begin
    with open(index_path, 'r+b') as index_file:
        mm = mmap.mmap(index_file.fileno(), 0)
        data = mm[begin:begin + length]
    return iterate(restore_bucket(data)[word])


class Variable:
    def __init__(self, name):
        self.name = name
        self.value = name

    def evaluate(self, index_path, urls_count, offsets):
        return restore(index_path, offsets, self.name)


class And:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.value = '&'

    def evaluate(self, index_path, urls_count, offsets):
        l = self.left.evaluate(index_path, urls_count, offsets)
        r = self.right.evaluate(index_path, urls_count, offsets)
        try:
            lv = next(l)
            rv = next(r)
            while True:
                if lv < rv:
                    lv = next(l)
                elif lv > rv:
                    rv = next(r)
                else:
                    yield lv
                    lv = next(l)
                    rv = next(r)
        except StopIteration:
            return


class Or:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.value = '|'

    def evaluate(self, index_path, urls_count, offsets):
        l = self.left.evaluate(index_path, urls_count, offsets)
        r = self.right.evaluate(index_path, urls_count, offsets)
        try:
            lv = next(l)
            try:
                rv = next(r)
            except StopIteration:
                yield lv
                raise StopIteration
            while True:
                if lv < rv:
                    yield lv
                    try:
                        lv = next(l)
                    except StopIteration:
                        yield rv
                        raise StopIteration
                elif lv > rv:
                    yield rv
                    try:
                        rv = next(r)
                    except StopIteration:
                        yield lv
                        raise StopIteration
                else:
                    yield lv
                    lv = next(l)
                    try:
                        rv = next(r)
                    except StopIteration:
                        yield lv
                        raise StopIteration
        except StopIteration:
            for e in l:
                yield e
            for e in r:
                yield e
            return


class Not:
    def __init__(self, name):
        self.name = name
        self.value = '!'

    def evaluate(self, index_path, urls_count, offsets):
        result = self.name.evaluate(index_path, urls_count, offsets)
        cur = 0
        for i in result:
            while cur < i:
                yield cur
                cur += 1
            cur += 1
        for i in range(cur, urls_count):
            yield i


def priorities(s):
    if s == '|':
        return 0
    if s == '&':
        return 1
    if s == '!':
        return 2
    return None


def get_tokens(q):
    return re.findall(r'\w+|[\(\)&\|!]', q, re.UNICODE)


def construct_tree(tokens):
    def parse_expression(ts):
        result, ts = parse_or(ts)
        while len(ts) > 0 and ts[0] == '|':
            ts = ts[1:]
            result_right, ts = parse_or(ts)
            result = Or(result, result_right)
        return result, ts

    def parse_or(ts):
        result, ts = parse_not(ts)
        while len(ts) > 0 and ts[0] == '&':
            ts = ts[1:]
            result_right, ts = parse_not(ts)
            result = And(result, result_right)
        return result, ts

    def parse_not(ts):
        if ts[0] == '(':
            ts = ts[1:]
            result, ts = parse_expression(ts)
            assert ts[0] == ')'
            ts = ts[1:]
            return result, ts
        elif ts[0] == '!':
            ts = ts[1:]
            result_right, ts = parse_not(ts)
            result = Not(result_right)
            return result, ts
        else:
            result = Variable(ts[0])
            ts = ts[1:]
            return result, ts

    result, tokens = parse_expression(tokens)
    assert len(tokens) == 0
    return result


def parse_query(q):
    tokens = get_tokens(q)
    return construct_tree(tokens)
