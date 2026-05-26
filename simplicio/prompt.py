"""prompt.py — empilha as 6 camadas."""
import os, re
from .precedent import montar_bloco_precedente
from .skill_router import montar_bloco_skill

def _mapper(root, alvo):
    try:
        txt = open(os.path.join(root, alvo), encoding="utf-8", errors="ignore").read()
    except Exception:
        return "(mapper: alvo nao lido)"
    deps = [l for l in txt.splitlines()
            if l.strip().startswith(("import", "using", "from"))][:15]
    return f"Arquivo: {alvo}\nDependencias:\n" + "\n".join(deps)

def montar(root, stack, objetivo, alvo, criterios, restricoes):
    tpl_path = os.path.join(os.path.dirname(__file__), "templates", "simplicio_prompt.md")
    tpl = open(tpl_path, encoding="utf-8").read()
    prec = montar_bloco_precedente(root, stack, objetivo, k=2)
    skill = montar_bloco_skill(root, objetivo)
    alvo_bloco = f"{alvo}\n\nContexto do alvo:\n{_mapper(root, alvo)}"
    for s, v in {"{{STACK}}": stack, "{{OBJETIVO}}": objetivo,
                 "{{ALVO}}": alvo_bloco, "{{PRECEDENTE}}": prec, "{{SKILL}}": skill,
                 "{{CRITERIOS}}": criterios, "{{RESTRICOES}}": restricoes}.items():
        tpl = tpl.replace(s, v)
    return re.sub(r"\{#.*?#\}", "", tpl, flags=re.DOTALL).strip()
