"""
bench.py — compara COM vs SEM o pipeline. Numeros REAIS, nada inventado.

Cada caso = {objetivo, alvo, criterios, test_cmd}.
  SEM:  manda so o objetivo cru pro LLM (baseline).
  COM:  pipeline completo (precedent + skill + camadas + verify).
Mede: passou no teste de primeira? quantas tentativas? 

Uso: simplicio bench --cases bench/cases.json --stack angular
Preenche bench/results.md com a tabela real.
"""
import os, json, time, subprocess
from .prompt import montar
from .providers import gerar

def _testa(saida, root, test_cmd):
    os.makedirs(os.path.join(root, ".simplicio"), exist_ok=True)
    open(os.path.join(root, ".simplicio/bench_out.txt"), "w").write(saida or "")
    p = subprocess.run(test_cmd, shell=True, cwd=root, capture_output=True, text=True)
    return p.returncode == 0

def _sem(caso, root):
    # baseline: objetivo cru, zero contexto montado
    return gerar(caso["objetivo"])

def _com(caso, root, stack):
    return gerar(montar(root, stack, caso["objetivo"], caso["alvo"],
                        caso.get("criterios","- estado verdadeiro\n- estado falso"),
                        caso.get("restricoes","- build passa")))

def run_bench(root, stack, cases_path):
    casos = json.load(open(cases_path))
    linhas, n = [], len(casos)
    acerto = {"sem": 0, "com": 0}
    for c in casos:
        tc = c["test_cmd"]
        ok_sem = _testa(_sem(c, root), root, tc); acerto["sem"] += ok_sem
        ok_com = _testa(_com(c, root, stack), root, tc); acerto["com"] += ok_com
        linhas.append(f"| {c['objetivo'][:40]} | {'✅' if ok_sem else '❌'} | {'✅' if ok_com else '❌'} |")
    tabela = ("| Tarefa | Sem simplicio | Com simplicio |\n|---|---|---|\n"
              + "\n".join(linhas)
              + f"\n\n**Acerto de primeira:** sem = {acerto['sem']}/{n} "
                f"({100*acerto['sem']//n}%) · com = {acerto['com']}/{n} "
                f"({100*acerto['com']//n}%)")
    out = os.path.join(root, "bench", "results.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(f"# Benchmark (gerado por `simplicio bench`)\n\n"
                         f"Provider: {os.environ.get('SIMPLICIO_PROVIDER','claude')} · "
                         f"casos: {n} · data: {time.strftime('%Y-%m-%d')}\n\n{tabela}\n")
    print(tabela)
    print(f"\n-> {out}")
