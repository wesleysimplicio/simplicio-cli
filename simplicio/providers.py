"""
providers.py — abstrai o LLM. Troca por env var, mesmo codigo.

  SIMPLICIO_PROVIDER = claude | gpt | glm | deepseek   (default: claude)

Claude usa SDK Anthropic. gpt/glm/deepseek usam API OpenAI-compativel
(base_url diferente) — por isso o mesmo cliente serve pros 3.
"""
import os

PROVIDERS = {
    "claude":   {"sdk": "anthropic", "model": "claude-opus-4-7"},
    "gpt":      {"sdk": "openai", "base": None,
                 "model": "gpt-4.1", "key_env": "OPENAI_API_KEY"},
    "glm":      {"sdk": "openai", "base": "https://api.z.ai/api/paas/v4",
                 "model": "glm-4.6", "key_env": "GLM_API_KEY"},
    "deepseek": {"sdk": "openai", "base": "https://api.deepseek.com",
                 "model": "deepseek-chat", "key_env": "DEEPSEEK_API_KEY"},
}

def gerar(prompt, feedback=None, max_tokens=4000):
    nome = os.environ.get("SIMPLICIO_PROVIDER", "claude").lower()
    cfg = PROVIDERS.get(nome, PROVIDERS["claude"])
    msgs = [{"role": "user", "content": prompt}]
    if feedback:
        msgs.append({"role": "user",
                     "content": f"O teste FALHOU:\n{feedback}\nCorrija. Mesmo formato."})

    if cfg["sdk"] == "anthropic":
        import anthropic
        c = anthropic.Anthropic()
        r = c.messages.create(model=cfg["model"], max_tokens=max_tokens, messages=msgs)
        return next((b.text for b in r.content if b.type == "text"), "")

    # OpenAI-compativel (gpt / glm / deepseek)
    from openai import OpenAI
    c = OpenAI(base_url=cfg.get("base"),
               api_key=os.environ.get(cfg["key_env"]))
    r = c.chat.completions.create(model=cfg["model"], max_tokens=max_tokens, messages=msgs)
    return r.choices[0].message.content
