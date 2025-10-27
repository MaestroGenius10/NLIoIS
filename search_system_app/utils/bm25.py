import math
from collections import Counter

class BM25:
    def __init__(self, documents, k1=1.5, b=0.75):
        """
        documents — список документов, где каждый документ представлен списком лемм
        k1, b — стандартные параметры BM25
        """
        self.documents = documents
        self.N = len(documents)
        self.avg_len = sum(len(doc) for doc in documents) / self.N
        self.k1 = k1
        self.b = b

        # Вычисляем DF для каждого термина
        self.df = {}
        for doc in documents:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

        # Предвычисляем IDF
        self.idf = {}
        for term, df in self.df.items():
            self.idf[term] = math.log((self.N - df + 0.5) / (df + 0.5) + 1)

    def score(self, query, doc):
        """
        query — список лемм запроса
        doc — список лемм документа
        """
        score = 0.0
        doc_len = len(doc)
        freqs = Counter(doc)
        for term in query:
            if term not in freqs:
                continue
            f = freqs[term]
            numerator = f * (self.k1 + 1)
            denominator = f + self.k1 * (1 - self.b + self.b * doc_len / self.avg_len)
            score += self.idf.get(term, 0) * numerator / denominator
        return score
