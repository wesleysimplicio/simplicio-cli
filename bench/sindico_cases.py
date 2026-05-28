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
]
