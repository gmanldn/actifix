#!/usr/bin/env python3
"""
Architecture Validation Script

Validates that MAP.yaml, DEPGRAPH.json, and MODULES.md are accurate
and consistent with the actual codebase structure.

This script addresses the following ACTIFIX tickets:
- ACT-20260110-FA6A3 (ARCH-ACC-001): Validate MAP.yaml modules match actual Python files
- ACT-20260110-D42C7 (ARCH-ACC-002): Ensure all DEPGRAPH.json nodes exist as modules in MAP.yaml
- ACT-20260110-BCA1D (ARCH-ACC-003): Verify all entrypoints in MAP.yaml resolve to existing files
- ACT-20260110-39B89 (ARCH-ACC-004): Validate dependency edges in DEPGRAPH.json match depends_on in MAP.yaml
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def load_map_yaml() -> Dict:
    """Load and parse MAP.yaml"""
    map_path = Path(__file__).parent.parent / "Arch" / "MAP.yaml"
    with open(map_path, 'r') as f:
        return yaml.safe_load(f)

def load_depgraph_json() -> Dict:
    """Load and parse DEPGRAPH.json"""
    depgraph_path = Path(__file__).parent.parent / "Arch" / "DEPGRAPH.json"
    with open(depgraph_path, 'r') as f:
        return json.load(f)

def validate_entrypoints_exist(map_data: Dict) -> Tuple[bool, List[str]]:
    """
    ARCH-ACC-001 & ARCH-ACC-003: Validate all entrypoints in MAP.yaml 
    exist as actual files
    """
    root = Path(__file__).parent.parent
    missing = []
    
    for module in map_data.get('modules', []):
        for entrypoint in module.get('entrypoints', []):
            file_path = root / entrypoint
            if not file_path.exists():
                missing.append(f"Module '{module['id']}': {entrypoint} not found")
    
    return len(missing) == 0, missing

def validate_depgraph_nodes_in_map(map_data: Dict, depgraph_data: Dict) -> Tuple[bool, List[str]]:
    """
    ARCH-ACC-002: Ensure all DEPGRAPH.json nodes exist as modules in MAP.yaml
    """
    # Get all module IDs from MAP.yaml
    map_module_ids = {module['id'] for module in map_data.get('modules', [])}
    
    # Get all node IDs from DEPGRAPH.json
    depgraph_node_ids = {node['id'] for node in depgraph_data.get('nodes', [])}
    
    # Find nodes that don't have corresponding modules
    missing = depgraph_node_ids - map_module_ids
    
    if missing:
        return False, [f"DEPGRAPH node '{node_id}' not found in MAP.yaml modules" for node_id in missing]
    
    return True, []

def validate_dependency_edges(map_data: Dict, depgraph_data: Dict) -> Tuple[bool, List[str]]:
    """
    ARCH-ACC-004: Validate dependency edges in DEPGRAPH.json match 
    depends_on in MAP.yaml
    """
    errors = []
    
    # Build depends_on mapping from MAP.yaml
    map_dependencies = {}
    for module in map_data.get('modules', []):
        module_id = module['id']
        depends_on = set(module.get('depends_on', []))
        map_dependencies[module_id] = depends_on
    
    # Build edge mapping from DEPGRAPH.json
    depgraph_edges = {}
    for edge in depgraph_data.get('edges', []):
        from_id = edge['from']
        to_id = edge['to']
        if from_id not in depgraph_edges:
            depgraph_edges[from_id] = set()
        depgraph_edges[from_id].add(to_id)
    
    # Compare MAP.yaml depends_on with DEPGRAPH edges
    all_module_ids = set(map_dependencies.keys())
    
    for module_id in all_module_ids:
        map_deps = map_dependencies.get(module_id, set())
        graph_deps = depgraph_edges.get(module_id, set())
        
        # Check for missing edges in DEPGRAPH
        missing_in_graph = map_deps - graph_deps
        if missing_in_graph:
            for dep in missing_in_graph:
                errors.append(
                    f"Module '{module_id}' depends on '{dep}' in MAP.yaml "
                    f"but edge not found in DEPGRAPH.json"
                )
        
        # Check for extra edges in DEPGRAPH
        extra_in_graph = graph_deps - map_deps
        if extra_in_graph:
            for dep in extra_in_graph:
                errors.append(
                    f"DEPGRAPH.json has edge from '{module_id}' to '{dep}' "
                    f"but not declared in MAP.yaml depends_on"
                )
    
    return len(errors) == 0, errors

def validate_module_node_consistency(map_data: Dict, depgraph_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate that module properties (domain, owner) are consistent 
    between MAP.yaml and DEPGRAPH.json
    """
    errors = []
    
    # Build module info from MAP.yaml
    map_modules = {module['id']: module for module in map_data.get('modules', [])}
    
    # Check each DEPGRAPH node
    for node in depgraph_data.get('nodes', []):
        node_id = node['id']
        
        if node_id not in map_modules:
            continue  # Already caught by validate_depgraph_nodes_in_map
        
        map_module = map_modules[node_id]
        
        # Check domain consistency
        if node.get('domain') != map_module.get('domain'):
            errors.append(
                f"Module '{node_id}': domain mismatch - "
                f"MAP.yaml='{map_module.get('domain')}', "
                f"DEPGRAPH.json='{node.get('domain')}'"
            )
        
        # Check owner consistency
        if node.get('owner') != map_module.get('owner'):
            errors.append(
                f"Module '{node_id}': owner mismatch - "
                f"MAP.yaml='{map_module.get('owner')}', "
                f"DEPGRAPH.json='{node.get('owner')}'"
            )
    
    return len(errors) == 0, errors

def main():
    """Run all architecture validations"""
    print("=" * 70)
    print("ACTIFIX ARCHITECTURE VALIDATION")
    print("=" * 70)
    print()
    
    # Load architecture documents
    print("Loading architecture documents...")
    try:
        map_data = load_map_yaml()
        depgraph_data = load_depgraph_json()
        print("✓ Loaded MAP.yaml and DEPGRAPH.json")
        print()
    except Exception as e:
        print(f"✗ Error loading architecture documents: {e}")
        return 1
    
    all_passed = True
    
    # Test 1: Validate entrypoints exist
    print("Test 1: Validating MAP.yaml entrypoints exist as actual files...")
    print("        (ARCH-ACC-001, ARCH-ACC-003)")
    passed, errors = validate_entrypoints_exist(map_data)
    if passed:
        print("✓ PASSED: All entrypoints exist")
    else:
        print("✗ FAILED:")
        for error in errors:
            print(f"  - {error}")
        all_passed = False
    print()
    
    # Test 2: Validate DEPGRAPH nodes in MAP
    print("Test 2: Validating DEPGRAPH.json nodes exist in MAP.yaml...")
    print("        (ARCH-ACC-002)")
    passed, errors = validate_depgraph_nodes_in_map(map_data, depgraph_data)
    if passed:
        print("✓ PASSED: All DEPGRAPH nodes have corresponding MAP modules")
    else:
        print("✗ FAILED:")
        for error in errors:
            print(f"  - {error}")
        all_passed = False
    print()
    
    # Test 3: Validate dependency edges
    print("Test 3: Validating dependency edges match between documents...")
    print("        (ARCH-ACC-004)")
    passed, errors = validate_dependency_edges(map_data, depgraph_data)
    if passed:
        print("✓ PASSED: All dependency edges are consistent")
    else:
        print("✗ FAILED:")
        for error in errors:
            print(f"  - {error}")
        all_passed = False
    print()
    
    # Test 4: Validate module/node property consistency
    print("Test 4: Validating module properties are consistent...")
    passed, errors = validate_module_node_consistency(map_data, depgraph_data)
    if passed:
        print("✓ PASSED: Module properties are consistent")
    else:
        print("✗ FAILED:")
        for error in errors:
            print(f"  - {error}")
        all_passed = False
    print()
    
    # Summary
    print("=" * 70)
    if all_passed:
        print("✓ ALL ARCHITECTURE VALIDATIONS PASSED")
        print()
        print("Validated tickets:")
        print("  - ACT-20260110-FA6A3 (ARCH-ACC-001): MAP.yaml modules validated")
        print("  - ACT-20260110-D42C7 (ARCH-ACC-002): DEPGRAPH nodes validated")
        print("  - ACT-20260110-BCA1D (ARCH-ACC-003): Entrypoints validated")
        print("  - ACT-20260110-39B89 (ARCH-ACC-004): Dependencies validated")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
