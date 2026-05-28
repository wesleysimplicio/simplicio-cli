"""
sindico_cases.py — real PHP modification tasks against sistema-sindico.

Each case asks the model to ADD a new method to an existing src/Core class.
Existing tests must keep passing (no breaking changes). Scoring is by REAL
PHPUnit (vendor/bin/phpunit) on the full suite plus a HIDDEN test (never shown
to the model) that asserts the new method's behaviour across true AND false
states. Pass == entire suite green.
"""
from __future__ import annotations

CASES = [
    {
        "id": "password_strength",
        "target": "src/Core/PasswordPolicy.php",
        "hidden_test": "PasswordStrengthTest.php",
        "goal": (
            "Add a NEW public static method `strength(string $password): string` "
            "to App\\Core\\PasswordPolicy that classifies the password as "
            "'weak', 'medium' or 'strong'."
        ),
        "criteria": (
            "- if `violations($password)` is not empty -> return 'weak'\n"
            "- otherwise, if `strlen($password) >= 12` AND the password contains "
            "at least one character from the set `!@#$%^&*` -> return 'strong'\n"
            "- otherwise -> return 'medium'\n"
            "- exact return values, lowercase: 'weak' | 'medium' | 'strong'"
        ),
        "constraints": (
            "- additive change: keep existing MIN_LENGTH, violations(), "
            "isValid(), describe() exactly as they are\n"
            "- pure function, no I/O\n"
            "- final class, namespace App\\Core, strict_types"
        ),
    },
    {
        "id": "password_require_symbol",
        "target": "src/Core/PasswordPolicy.php",
        "hidden_test": "PasswordRequireSymbolTest.php",
        "goal": (
            "Add a NEW public static method "
            "`requireSymbol(string $password): array` to App\\Core\\PasswordPolicy "
            "that reports whether the password contains a symbol."
        ),
        "criteria": (
            "- returns `['symbol']` when the password lacks every character "
            "from the set `!@#$%^&*`\n"
            "- returns `[]` when at least one such symbol is present\n"
            "- empty string returns `['symbol']`"
        ),
        "constraints": (
            "- additive change: keep existing MIN_LENGTH, violations(), "
            "isValid(), describe() exactly as they are\n"
            "- pure function, no I/O\n"
            "- final class, namespace App\\Core, strict_types"
        ),
    },
    {
        "id": "env_get_int",
        "target": "src/Core/Env.php",
        "hidden_test": "EnvGetIntTest.php",
        "goal": (
            "Add a NEW public static method "
            "`getInt(string $key, int $default = 0): int` to App\\Core\\Env "
            "that reads an environment variable and returns it as an integer."
        ),
        "criteria": (
            "- reads from `$_ENV[$key]` (falling back to `getenv($key)`)\n"
            "- returns the integer value when the env var is set AND is numeric "
            "(including negative integers like '-5')\n"
            "- returns `$default` when the env var is missing, empty, or non-numeric"
        ),
        "constraints": (
            "- additive change: keep the existing `load()` method and the "
            "global `env()` function exactly as they are\n"
            "- final class, namespace App\\Core, strict_types"
        ),
    },
    {
        "id": "env_get_bool",
        "target": "src/Core/Env.php",
        "hidden_test": "EnvGetBoolTest.php",
        "goal": (
            "Add a NEW public static method "
            "`getBool(string $key, bool $default = false): bool` to "
            "App\\Core\\Env that reads an environment variable and parses it "
            "as a boolean."
        ),
        "criteria": (
            "- reads from `$_ENV[$key]` (falling back to `getenv($key)`)\n"
            "- case-insensitive: '1', 'true', 'yes' -> true\n"
            "- case-insensitive: '0', 'false', 'no' -> false\n"
            "- missing, empty, or unrecognized value -> `$default`"
        ),
        "constraints": (
            "- additive change: keep the existing `load()` method and the "
            "global `env()` function exactly as they are\n"
            "- final class, namespace App\\Core, strict_types"
        ),
    },
    {
        "id": "admin_only_allowed_roles",
        "target": "src/Middleware/AdminOnly.php",
        "hidden_test": "AdminOnlyAllowedRolesTest.php",
        "goal": (
            "Add a NEW public static method `allowedRoles(): array` to "
            "App\\Middleware\\AdminOnly that returns the list of roles the "
            "middleware grants access to (the roles currently hardcoded in "
            "the existing handle() method)."
        ),
        "criteria": (
            "- returns exactly `['admin', 'sindico']`, in that order\n"
            "- callable statically as `AdminOnly::allowedRoles()`\n"
            "- public visibility"
        ),
        "constraints": (
            "- additive change: keep the existing handle() method unchanged\n"
            "- final class, namespace App\\Middleware, strict_types"
        ),
    },
    {
        "id": "rate_limit_bucket_key",
        "target": "src/Middleware/RateLimit.php",
        "hidden_test": "RateLimitBucketKeyTest.php",
        "goal": (
            "Add a NEW public static method "
            "`bucketKey(string $bucket, string $key): string` to "
            "App\\Middleware\\RateLimit that returns a normalized cache key."
        ),
        "criteria": (
            "- format: `'ratelimit:' + lowercase(bucket) + ':' + trim(key)`\n"
            "- bucketKey('login', 'user@example.com') -> "
            "'ratelimit:login:user@example.com'\n"
            "- bucketKey('VERIFY-CODE', '  user  ') -> "
            "'ratelimit:verify-code:user'\n"
            "- bucketKey('Login', \"\\tuser\\n\") -> 'ratelimit:login:user'"
        ),
        "constraints": (
            "- additive: keep existing enforce(), ipKey(), setStoreForTests() "
            "and private store() methods exactly as they are\n"
            "- final class, namespace App\\Middleware, strict_types"
        ),
    },
    {
        "id": "base_repository_build_where_sql",
        "target": "src/Repositories/BaseRepository.php",
        "hidden_test": "BaseRepositoryBuildWhereSqlTest.php",
        "goal": (
            "Add a NEW public static method "
            "`buildWhereSql(array $filters): array` to "
            "App\\Repositories\\BaseRepository that converts a filter map "
            "into a WHERE clause and bound parameters."
        ),
        "criteria": (
            "- returns `[$sql, $params]` where $sql is the WHERE clause "
            "WITHOUT the WHERE keyword and $params is an associative array "
            "of placeholder values\n"
            "- empty filters -> `['', []]`\n"
            "- `['name' => 'alice']` -> `['name = :name', ['name'=>'alice']]`\n"
            "- `['a'=>1, 'b'=>2]` -> `['a = :a AND b = :b', ['a'=>1,'b'=>2]]`\n"
            "- column names must match `/^[a-zA-Z_][a-zA-Z0-9_]*$/`; "
            "invalid column throws `InvalidArgumentException`"
        ),
        "constraints": (
            "- additive: keep the existing __construct, find(), all() and "
            "the private assertColumnName/sanitizeOrderBy helpers unchanged\n"
            "- abstract class, namespace App\\Repositories, strict_types\n"
            "- static method (no instance state needed)"
        ),
    },
    {
        "id": "router_has",
        "target": "src/Core/Router.php",
        "hidden_test": "RouterHasTest.php",
        "goal": (
            "Add a NEW public INSTANCE method "
            "`has(string $method, string $path): bool` to App\\Core\\Router "
            "that returns true iff at least one registered route has the "
            "same HTTP method AND a compiled regex that matches the given path."
        ),
        "criteria": (
            "- empty router: has('GET', '/x') -> false\n"
            "- after `$r->get('/api/health', ...)`: has('GET', '/api/health') "
            "-> true, has('POST', '/api/health') -> false\n"
            "- after `$r->get('/users/{id}', ...)`: has('GET', '/users/42') "
            "-> true (parameter routes match concrete paths)\n"
            "- has('GET', '/nonexistent') -> false"
        ),
        "constraints": (
            "- additive: keep get/post/put/patch/delete/group/dispatch and "
            "the private normalize/invoke/notFound helpers unchanged\n"
            "- INSTANCE method (uses $this->routes), not static\n"
            "- final class, namespace App\\Core, strict_types"
        ),
    },
]
