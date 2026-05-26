"""cli.py — comandos: index (cacheia repo) e task (roda o pipeline)."""
import argparse
from .precedent import index_repo
from .pipeline import run
from .bench import run_bench
from .providers import gerar, info

def main():
    ap = argparse.ArgumentParser(prog="simplicio")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("index", help="indexa/cacheia o repo (1x ou apos mudancas)")
    pi.add_argument("--root", default="."); pi.add_argument("--stack", default="angular")

    pt = sub.add_parser("task", help="executa uma tarefa")
    pt.add_argument("objetivo")
    pt.add_argument("--root", default="."); pt.add_argument("--stack", default="angular")
    pt.add_argument("--alvo", required=True)
    pt.add_argument("--criterios", default="- estado verdadeiro\n- estado falso")
    pt.add_argument("--restricoes", default="- build passa")


    pb = sub.add_parser("bench", help="compara com vs sem (numeros reais)")
    pb.add_argument("--root", default="."); pb.add_argument("--stack", default="angular")
    pb.add_argument("--cases", default="bench/cases.json")


    sub.add_parser("smoke", help="1 chamada de prova: conecta+gera (precisa SIMPLICIO_MODEL+KEY)")

    a = ap.parse_args()
    if a.cmd == "index":
        index_repo(a.root, a.stack)
    elif a.cmd == "smoke":
        print("provider:", info())
        out = gerar("Responda exatamente: OK simplicio conectado.")
        print("resposta do modelo:", out.strip()[:200])
    elif a.cmd == "bench":
        run_bench(a.root, a.stack, a.cases)
    else:
        run(a.root, a.stack, a.objetivo, a.alvo, a.criterios, a.restricoes)

if __name__ == "__main__":
    main()
