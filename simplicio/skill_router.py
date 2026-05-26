"""
skill_router.py — CAMADA 4.5. Seleciona A skill que casa com a tarefa.
NAO injeta todas (ruido). Ranqueia por sentido, pega top-1.

Fonte das skills: por padrao varre <root>/.mapper/skills/*.md ou
SIMPLICIO_SKILLS_DIR. Cada skill = arquivo md com 1a linha = descricao.
Reusa o mesmo cache de embeddings.
"""
import os, glob
import numpy as np
from .cache import EmbeddingCache

def _skills_dir(root):
    return os.environ.get("SIMPLICIO_SKILLS_DIR",
                          os.path.join(root, ".mapper", "skills"))

def _carregar_skills(root):
    d = _skills_dir(root)
    out = []
    for fp in glob.glob(os.path.join(d, "*.md")):
        try:
            txt = open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        desc = next((l.strip("# ").strip() for l in txt.splitlines() if l.strip()), "")
        out.append({"nome": os.path.basename(fp), "desc": desc, "corpo": txt})
    return out

def montar_bloco_skill(root, tarefa, limiar=0.15):
    skills = _carregar_skills(root)
    if not skills:
        return ""  # sem skills -> camada some, sem ruido
    from .precedent import _embedder
    cache = EmbeddingCache(root)
    descs = [s["desc"] for s in skills]
    faltam = cache.get_missing(descs)
    if faltam:
        cache.add(faltam, _embedder().encode(faltam, show_progress_bar=False))
        cache.save()
    vd = cache.lookup(descs)
    vt = _embedder().encode([tarefa])[0]
    scores = [float(np.dot(vt, v)/(np.linalg.norm(vt)*np.linalg.norm(v))) for v in vd]
    i = int(np.argmax(scores))
    if scores[i] < limiar:
        return ""  # nada casa o suficiente -> nao força skill irrelevante
    s = skills[i]
    return (f"[SKILL RELEVANTE]\nO mapper tem um metodo que casa com esta tarefa "
            f"(match {scores[i]:.2f}). Siga-o:\n# {s['nome']}\n{s['corpo'][:1200]}")
