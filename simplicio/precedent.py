"""
precedent.py — acha PRECEDENTE usando o cache (so embedda bloco novo).
"""
import re, glob, os
import numpy as np
from .cache import EmbeddingCache

_emb = None
def _embedder():
    global _emb
    if _emb is None:
        from sentence_transformers import SentenceTransformer
        _emb = SentenceTransformer("all-MiniLM-L6-v2")
    return _emb

PATTERNS = {
    "angular": [r"\*ngIf", r"\[hidden\]", r"\[disabled\]", r"hasPerm",
                r"ngxPermission", r"canActivate"],
    "react":   [r"&&\s*<", r"\?\s*<[A-Z]", r"usePermission", r"\bcan\(",
                r"hasRole", r"<Protected"],
    "dotnet":  [r"\[Authorize", r"HasPermission", r"User\.IsInRole",
                r"\[HasPolicy", r"RequireClaim"],
}
EXT = {"angular": (".html", ".ts"), "react": (".tsx", ".jsx", ".ts"),
       "dotnet": (".cs", ".cshtml", ".razor")}
SKIP = ("node_modules", "/.git/", "/dist/", "/bin/", "/obj/", "/.angular/", "/.simplicio/")


def grep_candidatos(root, stack, janela=1):
    pats = [re.compile(p) for p in PATTERNS[stack]]
    exts = EXT[stack]
    cands = []
    for fp in glob.glob(f"{root}/**/*", recursive=True):
        if not os.path.isfile(fp) or not fp.endswith(exts): continue
        if any(s in fp for s in SKIP): continue
        try:
            linhas = open(fp, encoding="utf-8", errors="ignore").read().splitlines()
        except Exception:
            continue
        for i, ln in enumerate(linhas):
            if any(p.search(ln) for p in pats):
                bloco = "\n".join(linhas[max(0, i - janela): i + janela + 1])
                cands.append({"file": fp, "line": i + 1, "code": bloco})
    return cands


def index_repo(root, stack, verbose=True):
    """Indexa: embedda SO os blocos novos, salva cache. Retorna stats."""
    cache = EmbeddingCache(root)
    cands = grep_candidatos(root, stack)
    textos = list({c["code"] for c in cands})         # dedup
    faltam = cache.get_missing(textos)
    if faltam:
        vetores = _embedder().encode(faltam, show_progress_bar=False)
        cache.add(faltam, vetores)
        cache.save()
    if verbose:
        print(f"[index] candidatos={len(cands)} novos_embeddados={len(faltam)} "
              f"cache_total={cache.stats()['cached_blocks']}")
    return cache, cands


def montar_bloco_precedente(root, stack, tarefa, k=2):
    cache, cands = index_repo(root, stack, verbose=False)
    if not cands:
        return "[PRECEDENTE]\n(nenhum padrao similar no repo — gere do zero pela convencao da stack)"
    textos = [c["code"] for c in cands]
    vc = cache.lookup(textos)                          # do cache, sem re-embeddar
    vt = _embedder().encode([tarefa])[0]               # so a tarefa (curta)
    for c, v in zip(cands, vc):
        c["score"] = float(np.dot(vt, v) / (np.linalg.norm(vt) * np.linalg.norm(v)))
    seen, out = set(), []
    for c in sorted(cands, key=lambda x: x["score"], reverse=True):
        if c["code"] in seen: continue
        seen.add(c["code"]); out.append(c)
    tops = out[:k]
    linhas = ["[PRECEDENTE]",
              "Este projeto JA faz algo parecido. Siga ESTA convencao, nao invente:"]
    for c in tops:
        rel = os.path.relpath(c["file"], root)
        linhas.append(f"\n# {rel}:{c['line']}  (similaridade {c['score']:.2f})")
        linhas.append(c["code"])
    return "\n".join(linhas)
