import sys
import cPickle

from doc2words import extract_words
from docreader import DocumentStreamReader
from simple9 import Simple9
from varbyte import VarByte
from parser import parse_query
from vocabulary import Vocabulary
import json


def serialize_bucket(index_file, words):
    s = ''
    s += '['
    for (w, v) in words:
        s += '('
        s += json.dumps(w)
        s += ','
        if type(v) == Simple9:
            s += json.dumps(v.elements).replace(' ', '')
        else:
            s += json.dumps(v.array.tolist())
        s += ')'
    s += ']'
    index_file.write(s)
    return len(s)


def dump(index_path, vocabulary):
    with open('id2url.pkl', 'wb') as id2url:
        cPickle.dump(vocabulary.url_from_id, id2url)
    N = 10**6
    offset = [0 for _ in range(N)]
    words = [[] for _ in range(N)]
    for word in vocabulary.url_ids.keys():
        bucket = hash(word) % N
        words[bucket].append((word, vocabulary.url_ids[word]))
    with open(index_path, 'wb') as index_file:
        cur_size = 0
        for bucket in range(N):
            offset[bucket] = cur_size
            cur_size += serialize_bucket(index_file, words[bucket])

    with open('offsets.pkl', 'wb') as offsets_file:
        for i in range(N):
            offsets_file.write(str(offset[i]) + '\n')


def create_index(args):
    reader = DocumentStreamReader(args[2:])
    if args[1] == 'varbyte':
        vocabulary = Vocabulary(Simple9)
    elif args[1] == 'simple9':
        vocabulary = Vocabulary(Simple9)
    else:
        raise AssertionError('Expected varbyte|simple9 as a compressor')

    for doc in reader:
        for word in extract_words(doc.text):
            vocabulary.append(word, doc.url)

    dump(args[0], vocabulary)


def main(index_path):
    #with open(index_path, 'rb') as index_data:
    #    vocabulary = cPickle.load(index_data)
    with open('id2url.pkl', 'rb') as id2url:
        url_from_id = cPickle.load(id2url)
    with open('offsets.pkl', 'rb') as offsets_file:
        lines = offsets_file.readlines()
        offset = []
        for line in lines:
            offset.append(int(line))
    while True:
        try:
            initial_query = raw_input()
            query = initial_query.decode('utf-8').lower()
            urls = parse_query(query).evaluate(index_path, len(url_from_id), offset)
            answer = map(url_from_id.__getitem__, urls)
            print(initial_query)
            print(len(answer))
            print('\n'.join(map(str, answer)))
        except EOFError:
            return


if __name__ == '__main__':
    if sys.argv[1] == 'create_index':
        create_index(sys.argv[2:])
    elif sys.argv[1] == 'perform_search':
        main(sys.argv[2])
    else:
        raise AssertionError('Usage: python main.py [create_index|perform_search] <index path> <arguments>')
