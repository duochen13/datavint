"""
Code Validator - AST-based security validation for generated code

Validates LLM-generated Python code for security before execution.
"""

import ast
from typing import Tuple

# Whitelist of allowed imports
ALLOWED_IMPORTS = {'datavint', 'pandas', 'numpy', 'vint', 'pd', 'np'}

# Blacklist of dangerous built-in functions
BLOCKED_BUILTINS = {'eval', 'exec', '__import__', 'compile', 'open', 'input', 'file'}


def validate_generated_code(code: str) -> Tuple[bool, str]:
    """
    Validate generated code for security.

    Performs AST-based validation to ensure code only uses allowed imports
    and does not call dangerous built-in functions.

    Security checks:
    - Syntax validity (AST parsing)
    - Import whitelist (only datavint, pandas, numpy)
    - Forbidden built-ins (eval, exec, open, etc.)

    Args:
        code: Generated Python code string

    Returns:
        Tuple of (is_valid, error_message):
        - (True, "Valid") if code passes all checks
        - (False, error_message) if code fails validation

    Examples:
        >>> validate_generated_code("import datavint as vint\\nstats, issues = vint.profile(df)")
        (True, "Valid")

        >>> validate_generated_code("import os\\nos.system('rm -rf /')")
        (False, "Forbidden import: os")

        >>> validate_generated_code("eval('malicious code')")
        (False, "Forbidden builtin: eval")
    """
    # Parse code into AST
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"

    # Walk the AST and check for violations
    for node in ast.walk(tree):
        # Check regular imports: import foo
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]  # Handle "pandas.core" as "pandas"
                if module_name not in ALLOWED_IMPORTS:
                    return False, f"Forbidden import: {alias.name}"

        # Check from imports: from foo import bar
        if isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]  # Handle "pandas.core" as "pandas"
                if module_name not in ALLOWED_IMPORTS:
                    return False, f"Forbidden import from: {node.module}"

        # Check function calls for dangerous built-ins
        if isinstance(node, ast.Call):
            # Direct builtin call: eval(...)
            if isinstance(node.func, ast.Name):
                if node.func.id in BLOCKED_BUILTINS:
                    return False, f"Forbidden builtin: {node.func.id}"

            # Attribute call on builtins: __builtins__.eval(...)
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in BLOCKED_BUILTINS:
                    return False, f"Forbidden builtin: {node.func.attr}"

    return True, "Valid"
