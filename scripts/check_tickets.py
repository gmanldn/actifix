#!/usr/bin/env python3
"""Check current tickets in the database."""
import sys
sys.path.insert(0, 'src')

from actifix.bootstrap import ActifixContext
from actifix.do_af import get_open_tickets

with ActifixContext():
    tickets = get_open_tickets()
    print(f'Open tickets: {len(tickets)}')
    for t in tickets[:10]:
        print(f'{t.ticket_id}: {t.message[:80]}... [P{t.priority}]')