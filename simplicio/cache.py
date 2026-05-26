"""
cache.py — cache de embeddings keyed por HASH do conteudo.

Por que por hash e nao por arquivo: se o bloco de codigo nao mudou, o hash
e o mesmo -> reusa o vetor. Arquivo muda mas o trecho relevante nao? Ainda
acerta o cache. Trecho muda -> hash novo -> re-embedda SO ele. Granular.

Persistido em .simplicio/emb_cache.npz (vetores) + .json (indice hash->linha).
"""

import os, json, hashlib
import numpy as np

class EmbeddingCache:
    def __init__(self, root):
        self.dir = os.path.join(root, ".simplicio")
        os.makedirs(self.dir, exist_ok=True)
        self.vec_path = os.path.join(self.dir, "emb_cache.npz")
        self.idx_path = os.path.join(self.dir, "emb_index.json")
        self.index = {}        # hash -> posicao na matriz
        self.vectors = None    # np.ndarray [N, dim]
        self._load()

    @staticmethod
    def h(texto):
        return hashlib.sha1(texto.encode("utf-8")).hexdigest()

    def _load(self):
        if os.path.exists(self.idx_path) and os.path.exists(self.vec_path):
            self.index = json.load(open(self.idx_path))
            self.vectors = np.load(self.vec_path)["v"]

    def save(self):
        json.dump(self.index, open(self.idx_path, "w"))
        if self.vectors is not None:
            np.savez_compressed(self.vec_path, v=self.vectors)

    def get_missing(self, textos):
        """Retorna os textos que NAO estao no cache (precisam embeddar)."""
        return [t for t in textos if self.h(t) not in self.index]

    def add(self, textos, vetores):
        """Adiciona novos textos+vetores ao cache."""
        if not textos:
            return
        vetores = np.asarray(vetores)
        base = 0 if self.vectors is None else self.vectors.shape[0]
        self.vectors = vetores if self.vectors is None else np.vstack([self.vectors, vetores])
        for i, t in enumerate(textos):
            self.index[self.h(t)] = base + i

    def lookup(self, textos):
        """Devolve matriz de vetores na ordem dos textos (todos ja no cache)."""
        rows = [self.index[self.h(t)] for t in textos]
        return self.vectors[rows]

    def stats(self):
        return {"cached_blocks": len(self.index),
                "dim": 0 if self.vectors is None else int(self.vectors.shape[1])}
