'''
ElMo BOW
fastText BOW
Glove BOW
BioWordVec BOW
Note GloVe Positional Encoding ?
'''

import io
import numpy as np
import sent2vec
from nltk import word_tokenize
from nltk.corpus import stopwords
from scipy.spatial import distance
from tqdm import tqdm
from typing import List

from scoler.scorer import Scorer


class WordEmbeddingSAVGScorer(Scorer):
    def __init__(self, use_word_vec_method):
        # ElMo BOW
        # fastText BOW
        # Glove BOW
        # BioWordVec BOW
        self.available_use_word_vec_methods = ['fasttext', 'glove']
        self.use_word_vec_method = use_word_vec_method
        self.vec_len = 50
        self.word_embeddings_dict = None
        # Note add a method_signature
        super().__init__('word-ebm-%s' % use_word_vec_method)
        self._read_all_word_vec_dict()

    def _read_all_word_vec_dict(self):
        word_embeddings_dict = {}
        if self.use_word_vec_method == 'glove':
            with open("/home/zhangli/pre-trained-models/glove.6B/glove.6B.%dd.txt" % self.vec_len, 'r') as f:
                for line in tqdm(f):
                    values = line.split()
                    word = values[0]
                    vector = np.asarray(values[1:], "float32")
                    word_embeddings_dict[word] = vector
        elif self.use_word_vec_method == 'fasttext':
            fin = io.open("/home/zhangli/pre-trained-models/wiki-news-300d-1M.vec", 'r', encoding='utf-8', newline='\n',
                          errors='ignore')
            n, d = map(int, fin.readline().split())
            for line in tqdm(fin):
                tokens = line.rstrip().split(' ')
                vector = np.asarray(tokens[1:], "float32")
                word_embeddings_dict[tokens[0]] = vector

        self.word_embeddings_dict = word_embeddings_dict

    def score(self, q_content: str, c_contents: List[str]) -> List[float]:
        if self.use_word_vec_method == 'biowordvec':
            return self.biosent_vec(q_content, c_contents)
        q_content_embedding = [self.word_embeddings_dict.get(n) for n in q_content.split(' ') if
                               n in self.word_embeddings_dict]
        q_content_embedding = self.pooling_word_embedding_to_sentence_embedding(q_content_embedding)
        scores = []
        for c_content in c_contents:
            c_content_embedding = [self.word_embeddings_dict.get(n) for n in c_content.split(' ') if
                                   n in self.word_embeddings_dict]
            c_content_embedding = self.pooling_word_embedding_to_sentence_embedding(c_content_embedding)
            score = 1 - distance.cosine(q_content_embedding, c_content_embedding)
            scores.append(score)
        return scores

    def biosent_vec(self, q_content, c_contents):
        # Note Load BioSentVec model
        model_path = '/home/zhangli/pre-trained-models/BioSentVec/BioSentVec_PubMed_MIMICIII-bigram_d700.bin'
        model = sent2vec.Sent2vecModel()
        try:
            model.load_model(model_path)
        except Exception as e:
            print(e)
        print('model successfully loaded')

        stop_words = set(stopwords.words('english'))

        def preprocess_sentence(text):
            text = text.replace('/', ' / ')
            text = text.replace('.-', ' .- ')
            text = text.replace('.', ' . ')
            text = text.replace('\'', ' \' ')
            text = text.lower()

            tokens = [token for token in word_tokenize(text) if token not in stop_words]

            return ' '.join(tokens)

        q_content_embedding = preprocess_sentence(q_content)
        scores = []
        for c_content in c_contents:
            c_content_embedding = model.embed_sentence(c_content)
            score = 1 - distance.cosine(q_content_embedding, c_content_embedding)
            scores.append(score)
        return scores

    def cosine_similarity(l1, l2):
        return 1 - distance.cosine(l1, l2)

    def pooling_word_embedding_to_sentence_embedding(self, emds):
        if emds is None or len(emds) == 0:
            return None
        else:
            emds = np.average([n for n in emds if n is not None], axis=0)
            if len(emds) == 0:
                return None
            else:
                return emds
