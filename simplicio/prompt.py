"""prompt.py — stacks the prompt layers."""
import os, re
from .adaptive import build_adaptation_block
from .mapper import build_mapper_context
from .precedent import build_precedent_block
from .skill_router import build_skill_block

def _mapper(root, target, goal=""):
    return build_mapper_context(root, target, goal=goal)

def build_prompt(root, stack, goal, target, criteria, constraints):
    tpl_path = os.path.join(os.path.dirname(__file__), "templates", "simplicio_prompt.md")
    tpl = open(tpl_path, encoding="utf-8").read()
    prec = build_precedent_block(root, stack, goal, k=2)
    skill = build_skill_block(root, goal)
    target_block = f"{target}\n\nTarget context:\n{_mapper(root, target, goal=goal)}"
    adaptation = build_adaptation_block(goal)
    for s, v in {"{{STACK}}": stack, "{{GOAL}}": goal,
                 "{{TARGET}}": target_block, "{{PRECEDENT}}": prec, "{{SKILL}}": skill,
                 "{{ADAPTATION}}": adaptation,
                 "{{CRITERIA}}": criteria, "{{CONSTRAINTS}}": constraints}.items():
        tpl = tpl.replace(s, v)
    return re.sub(r"\{#.*?#\}", "", tpl, flags=re.DOTALL).strip()
