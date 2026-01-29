import os
os.environ['ACTIFIX_CHANGE_ORIGIN'] = 'raise_af'
from actifix.do_af import mark_ticket_complete
mark_ticket_complete(
    ticket_id="ACT-20260125-3E33F",
    completion_notes="Implementation: `actifix modules validate` command validates module import, registration, metadata, and config parse (validate_module_package). Runs _discover_module_nodes, _lazy_import_module.\\nFiles:\\n- src/actifix/main.py (cmd_modules validate)\\n- src/actifix/modules/registry.py",
    test_steps="ACTIFIX_CHANGE_ORIGIN=raise_af python3 -m actifix.main modules validate",
    test_results="All modules OK: import success, metadata validation pass, config parse enforced. Matches ticket spec for smoke-test."
)