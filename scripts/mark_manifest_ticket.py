import os
os.environ['ACTIFIX_CHANGE_ORIGIN'] = 'raise_af'
from actifix.do_af import mark_ticket_complete
mark_ticket_complete(
    ticket_id="ACT-20260125-47C70",
    completion_notes="Implementation: Module scaffold generates MANIFEST.json with id, version, domain, dependencies as part of CLI `actifix modules create`. Verified in scaffold.py and test run.\nFiles:\n- src/actifix/modules/scaffold.py",
    test_steps="export ACTIFIX_CHANGE_ORIGIN=raise_af && python3 -m actifix.main modules create test_scaffold --force; inspect generated MANIFEST.json.",
    test_results="Confirmed: manifest created with {\"id\": \"modules.test_scaffold\", \"version\": \"0.1.0\", \"domain\": \"modules\", \"dependencies\": [...]}. Pre-commit tests pass."
)