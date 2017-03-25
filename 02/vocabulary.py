class Vocabulary:
    def __init__(self, compressor):
        self.url_ids = {}
        self.last_url = {}
        self.compressor = compressor
        self.id_from_url = {}
        self.url_from_id = {}

    def append(self, word, url):
        if url not in self.id_from_url:
            length = len(self.id_from_url)
            self.id_from_url[url] = length
            self.url_from_id[length] = url
        url_id = self.id_from_url[url]
        if word not in self.url_ids:
            self.last_url[word] = -1
            self.url_ids[word] = self.compressor()
        if self.last_url[word] != url_id:
            self.url_ids[word].append(url_id)
            self.last_url[word] = url_id

    def __getitem__(self, word):
        if word not in self.url_ids:
            return []
        return self.url_ids[word]

    def urls_count(self):
        return len(self.id_from_url)
