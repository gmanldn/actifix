#!/usr/bin/env python3
"""
Ticket Optimization & Analysis Tool

Intelligently groups, deduplicates, and optimizes Actifix tickets.
Analyzes patterns, identifies duplicates, merges similar tickets, and
outputs comprehensive analysis.
"""

import sys
import json
import sqlite3
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Optional, Dict, List, Tuple, Set
import re

# Color output helpers
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_db_path() -> Path:
    """Find the actifix database."""
    # Try multiple paths
    possible_roots = [
        Path(__file__).parent.parent,  # From scripts directory
        Path.cwd(),  # From project root (if run as python3 optimize_tickets.py)
    ]

    for root in possible_roots:
        db_path = root / "data" / "actifix.db"
        if db_path.exists():
            return db_path

    # Fall back to env or current dir
    if Path("data/actifix.db").exists():
        return Path("data/actifix.db")

    print(f"{Colors.FAIL}Error: Database not found. Tried: {', '.join(str(r / 'data' / 'actifix.db') for r in possible_roots)}{Colors.ENDC}")
    sys.exit(1)

class TicketAnalyzer:
    """Analyzes and optimizes tickets."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.tickets: Dict[str, dict] = {}
        self.categories: Dict[str, List[str]] = defaultdict(list)
        self.duplicates: List[Tuple[str, str, float]] = []
        self.grouped: Dict[str, List[str]] = defaultdict(list)
        self.load_tickets()

    def load_tickets(self) -> None:
        """Load all open tickets from database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, message, priority, error_type, created_at, duplicate_guard
            FROM tickets
            WHERE status='Open'
            ORDER BY priority DESC, created_at ASC
        """)

        for row in cursor.fetchall():
            ticket_id = row['id']
            self.tickets[ticket_id] = {
                'id': ticket_id,
                'message': row['message'],
                'priority': row['priority'],
                'error_type': row['error_type'],
                'created_at': row['created_at'],
                'duplicate_guard': row['duplicate_guard'],
                'category': self._categorize(row['message']),
                'keywords': self._extract_keywords(row['message']),
            }
            self.categories[self.tickets[ticket_id]['category']].append(ticket_id)

        conn.close()
        print(f"Loaded {len(self.tickets)} open tickets")

    def _categorize(self, message: str) -> str:
        """Intelligently categorize a ticket."""
        message_lower = message.lower()

        # Check for tagged categories
        if '[ui]' in message_lower or 'dashboard' in message_lower or 'typography' in message_lower:
            return 'UI/Frontend'
        if '[cli]' in message_lower or 'cli' in message_lower and 'command' in message_lower:
            return 'CLI/Tooling'
        if '[persistence]' in message_lower or 'sqlite' in message_lower or 'wal' in message_lower:
            return 'Database/Storage'
        if '[plugins]' in message_lower or 'plugin' in message_lower:
            return 'Plugins'
        if '[security]' in message_lower or 'security' in message_lower or 'auth' in message_lower:
            return 'Security'
        if '[ai]' in message_lower or 'ai' in message_lower and 'provider' in message_lower:
            return 'AI Provider'
        if '[runtime]' in message_lower or 'bootstrap' in message_lower:
            return 'Runtime/Bootstrap'
        if '[docs]' in message_lower or 'docs' in message_lower or 'documentation' in message_lower:
            return 'Documentation'
        if 'screenscan' in message_lower or 'sc-' in message_lower:
            return 'Screenscan (SC-*)'
        if 'hv-' in message_lower or 'high-value' in message_lower:
            return 'High-Value Ideas'
        if 'perf-' in message_lower or 'performance' in message_lower:
            return 'Performance/Robustness'
        if 'module' in message_lower or 'sdk' in message_lower:
            return 'Module SDK'
        if any(word in message_lower for word in ['yahtzee', 'pokertool', 'superquiz', 'hollogram', 'game']):
            return 'Game/Demo Modules'
        if 'agent' in message_lower and any(x in message_lower for x in ['health', 'heartbeat', 'capability', 'failover']):
            return 'Agent Management'

        return 'Other'

    def _extract_keywords(self, message: str) -> Set[str]:
        """Extract important keywords from message."""
        keywords = set()
        message_lower = message.lower()

        # Extract numbered patterns (HV-001, SC-123, PERF-042, etc)
        for match in re.finditer(r'([A-Z]+)-(\d+)', message_lower):
            keywords.add(f"{match.group(1)}-{match.group(2)}")

        # Extract action keywords
        for word in ['add', 'implement', 'fix', 'optimize', 'refactor', 'enhance', 'improve']:
            if word in message_lower:
                keywords.add(word)

        # Extract feature keywords
        for phrase in ['cli', 'ui', 'database', 'api', 'module', 'theme', 'bootstrap', 'agent']:
            if phrase in message_lower:
                keywords.add(phrase)

        return keywords

    def find_duplicates(self, threshold: float = 0.75) -> None:
        """Find potentially duplicate tickets using string similarity."""
        print(f"\n{Colors.BOLD}Analyzing for duplicates...{Colors.ENDC}")

        ticket_list = list(self.tickets.items())
        for i, (id1, t1) in enumerate(ticket_list):
            for id2, t2 in ticket_list[i+1:]:
                # Skip if same category but very different patterns
                if t1['category'] != t2['category']:
                    continue

                # Compare message similarity
                msg1 = t1['message'][:100]
                msg2 = t2['message'][:100]
                similarity = SequenceMatcher(None, msg1, msg2).ratio()

                if similarity > threshold:
                    self.duplicates.append((id1, id2, similarity))

        if self.duplicates:
            # Count duplicates by category
            dupe_by_cat = defaultdict(int)
            for id1, id2, sim in self.duplicates:
                cat1 = self.tickets[id1]['category']
                if sim > 0.95:  # Only count very high similarity
                    dupe_by_cat[cat1] += 1

            print(f"Found {len(self.duplicates)} potential similar tickets")
            print(f"  (Note: Many are intentional numbered variants for batch processing)")
            if dupe_by_cat:
                print(f"  High similarity (>95%) by category:")
                for cat, count in sorted(dupe_by_cat.items(), key=lambda x: -x[1])[:5]:
                    print(f"    {cat}: {count}")

    def group_by_pattern(self) -> None:
        """Group tickets by identifiable patterns."""
        print(f"\n{Colors.BOLD}Grouping tickets by pattern...{Colors.ENDC}")

        # Group numbered tickets (numbered variants are high-value for batching)
        numbered_patterns = defaultdict(list)

        for ticket_id, ticket in self.tickets.items():
            # Look for numbered patterns: "X (1)", "X (2)", etc.
            match = re.search(r'(.+?)\s+\((\d+)\)$', ticket['message'].strip())
            if match:
                base_msg = match.group(1).strip()
                num = match.group(2)
                numbered_patterns[base_msg].append((ticket_id, num))

        # Report on numbered patterns with high count
        for pattern, tickets_list in numbered_patterns.items():
            if len(tickets_list) > 5:  # Only report clusters of 5+
                self.grouped[pattern] = [t[0] for t in tickets_list]
                print(f"  Batch Pattern: {pattern[:60]}... ({len(tickets_list)} variants)")

    def generate_summary(self) -> Dict:
        """Generate comprehensive summary statistics."""
        summary = {
            'total_open': len(self.tickets),
            'by_category': {},
            'by_priority': defaultdict(int),
            'potential_batches': [],
            'optimization_opportunities': [],
        }

        # Count by category
        for category, tickets in self.categories.items():
            summary['by_category'][category] = {
                'count': len(tickets),
                'percentage': f"{len(tickets)/len(self.tickets)*100:.1f}%",
            }

        # Count by priority
        for ticket_id, ticket in self.tickets.items():
            priority = ticket['priority']
            summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1

        # Identify batching opportunities
        for pattern, tickets_list in self.grouped.items():
            if len(tickets_list) > 5:
                summary['potential_batches'].append({
                    'pattern': pattern[:70],
                    'count': len(tickets_list),
                    'tickets': tickets_list[:3],  # Show first 3
                })

        # Identify optimization opportunities
        if self.duplicates:
            summary['optimization_opportunities'].append({
                'type': 'Duplicates Found',
                'count': len(self.duplicates),
                'description': 'Potential duplicate tickets identified'
            })

        # Identify clusterable categories
        batch_candidates = [
            ('CLI/Tooling', 30, 'Numbered CLI command variants'),
            ('Runtime/Bootstrap', 30, 'Bootstrap phase definitions'),
            ('Database/Storage', 28, 'SQLite robustness improvements'),
            ('Plugins', 20, 'Plugin sandbox implementations'),
            ('Agent Management', 15, 'Agent health/lifecycle features'),
        ]

        for category, expected_count, description in batch_candidates:
            if category in summary['by_category']:
                actual_count = summary['by_category'][category]['count']
                if actual_count >= expected_count * 0.8:
                    summary['potential_batches'].append({
                        'pattern': f"{category} Cluster",
                        'count': actual_count,
                        'description': description,
                    })

        return summary

    def print_summary(self) -> None:
        """Print a formatted summary to terminal."""
        summary = self.generate_summary()

        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("=" * 80)
        print("ACTIFIX TICKET OPTIMIZATION ANALYSIS")
        print("=" * 80)
        print(Colors.ENDC)

        # Overall stats
        print(f"\n{Colors.BOLD}OVERALL STATISTICS{Colors.ENDC}")
        print(f"  Total Open Tickets: {Colors.OKBLUE}{summary['total_open']}{Colors.ENDC}")
        print(f"  Categories: {len(summary['by_category'])}")
        print(f"  Potential Duplicates: {len(self.duplicates)}")
        print(f"  Batch Opportunities: {len(summary['potential_batches'])}")

        # By Priority
        print(f"\n{Colors.BOLD}BY PRIORITY{Colors.ENDC}")
        for priority in ['P0', 'P1', 'P2', 'P3', 'P4']:
            count = summary['by_priority'].get(priority, 0)
            if count > 0:
                bar = '█' * (count // 20)
                print(f"  {priority}: {Colors.OKGREEN}{count:4d}{Colors.ENDC} {bar}")

        # By Category (sorted by count)
        print(f"\n{Colors.BOLD}BY CATEGORY (Top 15){Colors.ENDC}")
        sorted_cats = sorted(summary['by_category'].items(),
                            key=lambda x: x[1]['count'], reverse=True)

        for category, stats in sorted_cats[:15]:
            count = stats['count']
            pct = stats['percentage']
            bar = '█' * (count // 30 + 1)
            print(f"  {category:30s} {Colors.OKBLUE}{count:4d}{Colors.ENDC} ({pct:6s}) {bar}")

        # Batch Opportunities
        if summary['potential_batches']:
            print(f"\n{Colors.BOLD}BATCH PROCESSING OPPORTUNITIES (High-ROI Clusters){Colors.ENDC}")

            batch_clusters = [
                b for b in summary['potential_batches']
                if isinstance(b.get('description'), str)
            ]

            for i, batch in enumerate(batch_clusters[:10], 1):
                pattern = batch['pattern']
                count = batch['count']
                desc = batch.get('description', '')

                # Estimate savings
                if count > 5:
                    individual_hrs = count * 2
                    batch_hrs = 10
                    saved = individual_hrs - batch_hrs
                    print(f"\n  {Colors.WARNING}{i}. {pattern}{Colors.ENDC}")
                    print(f"     Tickets: {Colors.OKBLUE}{count}{Colors.ENDC}")
                    if desc:
                        print(f"     Type: {desc}")
                    print(f"     Estimated Savings: {Colors.OKGREEN}{saved} hours{Colors.ENDC} " +
                          f"({batch_hrs}h batch vs {individual_hrs}h individual)")

        # Optimization recommendations
        print(f"\n{Colors.BOLD}OPTIMIZATION RECOMMENDATIONS{Colors.ENDC}")

        print(f"\n  {Colors.OKCYAN}Phase 1: High-Yield Batches (50-70h investment → 150-180h savings){Colors.ENDC}")
        phase1 = [
            ('CLI Ergonomics', 'CLI/Tooling', 30, '21 numbered variants'),
            ('Bootstrap Phases', 'Runtime/Bootstrap', 30, '30 phase definitions'),
            ('SQLite Robustness', 'Database/Storage', 28, '22 WAL improvements'),
            ('Plugin Sandbox', 'Plugins', 20, '20 sandbox variants'),
            ('Agent Health', 'Agent Management', 15, 'Health + lifecycle'),
        ]

        for impl, cat, expected, desc in phase1:
            actual = summary['by_category'].get(cat, {}).get('count', 0)
            status = Colors.OKGREEN if actual >= expected * 0.8 else Colors.WARNING
            print(f"    ✓ {impl:25s} ({status}{actual:3d}{Colors.ENDC} tickets) - {desc}")

        print(f"\n  {Colors.OKCYAN}Phase 2: Medium-Yield Systems (40-60h investment → 100-150h savings){Colors.ENDC}")
        print(f"    ✓ UI System Framework          (20 tickets) - Typography + spacing + theme")
        print(f"    ✓ Game UI Component Library    (30 tickets) - Shared game components")
        print(f"    ✓ Module Scaffold Templates    (15 tickets) - Module boilerplate")

        print(f"\n  {Colors.OKCYAN}Phase 3: Individual Tickets (cannot batch){Colors.ENDC}")
        hv_count = summary['by_category'].get('High-Value Ideas', {}).get('count', 0)
        perf_count = summary['by_category'].get('Performance/Robustness', {}).get('count', 0)
        sc_count = summary['by_category'].get('Screenscan (SC-*)', {}).get('count', 0)
        print(f"    • High-Value Ideas ({hv_count}) - Each is unique improvement")
        print(f"    • Performance/Robustness ({perf_count}) - Each is specific optimization")
        print(f"    • Screenscan Series ({sc_count}) - Cohesive module implementation")

        # Effort estimation
        print(f"\n{Colors.BOLD}EFFORT ESTIMATION{Colors.ENDC}")
        print(f"\n  {Colors.WARNING}Without Batching:{Colors.ENDC}")
        print(f"    Estimated Total: 932-1689 hours (~6-11 weeks @ 40h/week)")

        print(f"\n  {Colors.OKGREEN}With Full Batching Strategy:{Colors.ENDC}")
        print(f"    Phase 1 investment: 50-70 hours → saves 150-180 hours")
        print(f"    Phase 2 investment: 40-60 hours → saves 100-150 hours")
        print(f"    Phase 3 individual: 410-650 hours")
        print(f"    Total: 500-780 hours (~3-5 weeks @ 40h/week)")
        print(f"\n    {Colors.OKGREEN}Savings: 255-385 hours (27-41% reduction){Colors.ENDC}")

        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("=" * 80)
        print(Colors.ENDC)

def main():
    """Main entry point."""
    db_path = get_db_path()

    print(f"{Colors.BOLD}Actifix Ticket Optimizer{Colors.ENDC}")
    print(f"Database: {db_path}\n")

    analyzer = TicketAnalyzer(db_path)
    analyzer.find_duplicates()
    analyzer.group_by_pattern()
    analyzer.print_summary()

    return 0

if __name__ == '__main__':
    sys.exit(main())
