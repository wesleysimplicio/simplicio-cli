# v13 INTERIM — bench em andamento (snapshot dos logs ao vivo)

Captura: **2026-05-30 21:46:45**

Parser dos logs `/tmp/exec_v13.log` e `/tmp/regex_v13.log`. Modelos com linha `-> baseline …` ESTÃO completos; modelos sem ela ainda rodam (mostro o que veio até agora).

## Sides

- `sem`  = baseline (raw goal)
- `com`  = cli alone (6-layer contract)
- `sp`   = cli + sp (composition)
- `ag`   = cli + ag (verify-loop max 3 attempts)
- `spag` = cli + sp + ag (composition + verify-loop)

## Headline — fechados (`-> baseline ...`)

### `llama-3.2-3b-instruct`

| metric | base | cli | cli+sp | cli+ag | cli+sp+ag | Δcli | Δsp | Δag | Δsp+ag |
|---|---|---|---|---|---|---|---|---|---|
| exec  (n=12)  | 8% | 8% | 8% | 8% | 8% | **+0** | **+0** | **+0** | **+0** |
| regex (t=52) | 32% | 69% | 67% | 88% | 76% | **+37** | **+35** | **+56** | **+44** |


## Em andamento (parcial)

### `gemma-3-4b-it`

**exec** progresso: 6/12  base=1  cli=5  cli+sp=4  cli+ag=5  cli+sp+ag=3
**regex** progresso: 5/10  base=8/26  cli=25/26  cli+sp=24/26  cli+ag=25/26  cli+sp+ag=24/26


## Per-task exec (modelos fechados)

Format: `b/c/s/a/sa` (P=pass, .=fail)

| Task | llama-3.2-3b-instruct |
|---|---|
| `password_strength` | ././././. |
| `password_require_symbol` | ././././. |
| `env_get_int` | ././././. |
| `env_get_bool` | ././././. |
| `admin_only_allowed_roles` | P/P/P/P/P |
| `rate_limit_bucket_key` | ././././. |
| `base_repository_build_where_sql` | ././././. |
| `router_has` | ././././. |
| `bugfix_password_policy_lowercase` | ././././. |
| `password_assess` | ././././. |
| `base_repository_build_update_sql` | ././././. |
| `router_extract_params` | ././././. |
