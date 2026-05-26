"""pipeline.py — monta -> gera -> aplica -> testa -> corrige (loop)."""
import os, subprocess
from .prompt import montar
from .providers import gerar

MAX_TENTATIVAS = 3

def _aplicar_e_testar(saida, root):
    os.makedirs(os.path.join(root, ".simplicio"), exist_ok=True)
    open(os.path.join(root, ".simplicio/ultima_saida.txt"), "w").write(saida)
    # PLUGUE: extrair diff -> git apply; extrair teste. Aqui roda o cmd de teste.
    cmd = os.environ.get("SIMPLICIO_TEST_CMD", "echo 'configure SIMPLICIO_TEST_CMD'")
    p = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr)[-2000:]

def run(root, stack, objetivo, alvo, criterios, restricoes):
    prompt = montar(root, stack, objetivo, alvo, criterios, restricoes)
    feedback = None
    for t in range(1, MAX_TENTATIVAS + 1):
        print(f"--- tentativa {t} (provider={os.environ.get('SIMPLICIO_PROVIDER','claude')}) ---")
        saida = gerar(prompt, feedback)
        ok, log = _aplicar_e_testar(saida, root)
        if ok:
            print("PASSOU no contrato. PRONTO.")
            return saida
        print("falhou:", log[:300]); feedback = log
    print("esgotou tentativas — revisar manual.")
    return None
