import os
os.environ['ACTIFIX_CHANGE_ORIGIN'] = 'raise_af'
from actifix.do_af import mark_ticket_complete
mark_ticket_complete(
    ticket_id="ACT-20260125-3E33F",
    completion_notes="Implementation: `actifix modules validate` provides smoke-test for module import, registration, metadata validation (incl. config parse via validate_module_package).\\nFiles:\\n- src/actifix/main.py (cmd_modules validate)\\n- src/actifix/modules/registry.py (_discover_module_nodes, _lazy_import_module, validate_module_package)",
    test_steps="ACTIFIX_CHANGE_ORIGIN=raise_af python3 -m actifix.main modules validate",
    test_results="Validates all modules: import success, metadata OK, config parse enforced. Pre-commit tests pass."
)