"""
providers.py — agnostico de provider. NAO lista modelos especificos.

Voce define por env (ou flag --model/--base):
  SIMPLICIO_MODEL     id do modelo, exatamente como o provider espera
                      ex: "anthropic/claude-opus-4", "openai/gpt-4.1",
                          "z-ai/glm-4.6", "deepseek/deepseek-chat", "qualquer/coisa"
  SIMPLICIO_BASE_URL  endpoint OpenAI-compativel
                      ex OpenRouter: https://openrouter.ai/api/v1
                      ex GLM:        https://api.z.ai/api/paas/v4
                      ex local:      http://localhost:11434/v1
  SIMPLICIO_API_KEY   a chave (qualquer provider)

Caminho nativo Anthropic (sem base_url): se SIMPLICIO_BASE_URL estiver vazio
E a key for ANTHROPIC_API_KEY, usa o SDK anthropic. Senao, usa cliente
OpenAI-compativel apontando pro base_url -> serve QUALQUER provider OAI-like.
"""
import os

def _cfg():
    return {
        "model": os.environ.get("SIMPLICIO_MODEL"),
        "base":  os.environ.get("SIMPLICIO_BASE_URL"),
        "key":   os.environ.get("SIMPLICIO_API_KEY")
                 or os.environ.get("OPENROUTER_API_KEY")
                 or os.environ.get("ANTHROPIC_API_KEY"),
    }

def _msgs(prompt, feedback):
    m = [{"role": "user", "content": prompt}]
    if feedback:
        m.append({"role": "user",
                  "content": f"O teste FALHOU:\n{feedback}\nCorrija. Mesmo formato."})
    return m

def gerar(prompt, feedback=None, max_tokens=4000):
    c = _cfg()
    if not c["model"]:
        raise SystemExit("defina SIMPLICIO_MODEL (id do modelo do seu provider)")
    if not c["key"]:
        raise SystemExit("defina SIMPLICIO_API_KEY (ou OPENROUTER_/ANTHROPIC_API_KEY)")

    # caminho nativo Anthropic: sem base_url
    if not c["base"]:
        import anthropic
        cli = anthropic.Anthropic(api_key=c["key"])
        r = cli.messages.create(model=c["model"], max_tokens=max_tokens,
                                messages=_msgs(prompt, feedback))
        return next((b.text for b in r.content if b.type == "text"), "")

    # qualquer endpoint OpenAI-compativel (OpenRouter, GLM, DeepSeek, local...)
    from openai import OpenAI
    cli = OpenAI(base_url=c["base"], api_key=c["key"])
    r = cli.chat.completions.create(model=c["model"], max_tokens=max_tokens,
                                    messages=_msgs(prompt, feedback))
    return r.choices[0].message.content

def info():
    c = _cfg()
    return (f"model={c['model'] or '(nao definido)'} "
            f"base={c['base'] or 'anthropic-nativo'} "
            f"key={'set' if c['key'] else 'FALTA'}")
