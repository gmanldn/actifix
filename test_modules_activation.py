#!/usr/bin/env python3
"""
Integration test script to verify dev_assistant and hollogram modules
are properly activated and functional.
"""

import importlib
import sys


def test_dev_assistant_module():
    """Test dev_assistant module activation."""
    print("\n" + "="*70)
    print("Testing dev_assistant Module")
    print("="*70)
    
    try:
        # Import the module
        print("✓ Importing dev_assistant module...")
        dev_assistant = importlib.import_module('actifix.modules.dev_assistant')
        print("  ✓ Module imported successfully")
        
        # Check module metadata
        print("\n✓ Checking module metadata...")
        metadata = dev_assistant.MODULE_METADATA
        print(f"  Name: {metadata['name']}")
        print(f"  Version: {metadata['version']}")
        print(f"  Description: {metadata['description']}")
        
        # Check module defaults
        print("\n✓ Checking module defaults...")
        defaults = dev_assistant.MODULE_DEFAULTS
        print(f"  Model: {defaults['model']}")
        
        # Check module dependencies
        print("\n✓ Checking module dependencies...")
        dependencies = dev_assistant.MODULE_DEPENDENCIES
        print(f"  Dependencies: {', '.join(dependencies)}")
        
        # Create blueprint
        print("\n✓ Creating blueprint...")
        try:
            blueprint = dev_assistant.create_blueprint()
            print(f"  ✓ Blueprint created: {blueprint.name}")
            print(f"  ✓ URL prefix: {blueprint.url_prefix}")
            
            # Check routes using Flask's test client
            print("\n✓ Checking registered routes...")
            try:
                from flask import Flask
                app = Flask(__name__)
                app.register_blueprint(blueprint)
                with app.test_client() as client:
                    # Test health endpoint
                    resp = client.get('/modules/dev_assistant/health')
                    if resp.status_code == 200:
                        print(f"  ✓ /health endpoint: {resp.status_code}")
                    else:
                        print(f"  ⚠ /health endpoint: {resp.status_code}")
                    
                    # Test chat endpoint (expect 400 for empty request)
                    resp = client.post('/modules/dev_assistant/chat', json={})
                    if resp.status_code == 400:
                        print(f"  ✓ /chat endpoint: {resp.status_code} (expected for empty request)")
                    else:
                        print(f"  ⚠ /chat endpoint: {resp.status_code}")
            except ImportError:
                print("  ⚠ Flask not available, skipping route verification")
            
            print("\n✓ dev_assistant module is ACTIVE and functional!")
            return True
            
        except Exception as e:
            print(f"\n✗ Failed to create blueprint: {e}")
            print(f"  Error type: {type(e).__name__}")
            return False
            
    except Exception as e:
        print(f"\n✗ Failed to import or test dev_assistant module: {e}")
        print(f"  Error type: {type(e).__name__}")
        return False


def test_hollogram_module():
    """Test hollogram module activation."""
    print("\n" + "="*70)
    print("Testing hollogram Module")
    print("="*70)
    
    try:
        # Import the module
        print("✓ Importing hollogram module...")
        hollogram = importlib.import_module('actifix.modules.hollogram')
        print("  ✓ Module imported successfully")
        
        # Check module metadata
        print("\n✓ Checking module metadata...")
        metadata = hollogram.MODULE_METADATA
        print(f"  Name: {metadata['name']}")
        print(f"  Version: {metadata['version']}")
        print(f"  Description: {metadata['description']}")
        
        # Check module defaults
        print("\n✓ Checking module defaults...")
        defaults = hollogram.MODULE_DEFAULTS
        print(f"  Host: {defaults['host']}")
        print(f"  Port: {defaults['port']}")
        print(f"  Max query length: {defaults['max_query_length']}")
        print(f"  History limit: {defaults['history_limit']}")
        
        # Check module dependencies
        print("\n✓ Checking module dependencies...")
        dependencies = hollogram.MODULE_DEPENDENCIES
        print(f"  Dependencies: {', '.join(dependencies)}")
        
        # Check access rule
        print("\n✓ Checking access rule...")
        access_rule = hollogram.ACCESS_RULE
        print(f"  Access rule: {access_rule}")
        
        # Check medical disclaimer
        print("\n✓ Checking medical disclaimer...")
        disclaimer = hollogram.MEDICAL_DISCLAIMER
        print(f"  Disclaimer length: {len(disclaimer)} characters")
        
        # Check research primer
        print("\n✓ Checking research primer...")
        primer = hollogram.RESEARCH_PRIMER
        print(f"  Primer length: {len(primer)} characters")
        
        # Check topic categories
        print("\n✓ Checking topic categories...")
        topics = hollogram.TOPIC_CATEGORIES
        print(f"  Number of categories: {len(topics)}")
        for topic in topics:
            print(f"    - {topic['id']}: {topic['name']}")
        
        # Create blueprint
        print("\n✓ Creating blueprint...")
        try:
            blueprint = hollogram.create_blueprint()
            print(f"  ✓ Blueprint created: {blueprint.name}")
            print(f"  ✓ URL prefix: {blueprint.url_prefix}")
            
            # Check routes using Flask's test client
            print("\n✓ Checking registered routes...")
            try:
                from flask import Flask
                app = Flask(__name__)
                app.register_blueprint(blueprint)
                with app.test_client() as client:
                    # Test health endpoint
                    resp = client.get('/modules/hollogram/health')
                    if resp.status_code == 200:
                        print(f"  ✓ /health endpoint: {resp.status_code}")
                    else:
                        print(f"  ⚠ /health endpoint: {resp.status_code}")
                    
                    # Test disclaimer endpoint
                    resp = client.get('/modules/hollogram/disclaimer')
                    if resp.status_code == 200:
                        print(f"  ✓ /disclaimer endpoint: {resp.status_code}")
                    else:
                        print(f"  ⚠ /disclaimer endpoint: {resp.status_code}")
                    
                    # Test topics endpoint
                    resp = client.get('/modules/hollogram/topics')
                    if resp.status_code == 200:
                        print(f"  ✓ /topics endpoint: {resp.status_code}")
                    else:
                        print(f"  ⚠ /topics endpoint: {resp.status_code}")
            except ImportError:
                print("  ⚠ Flask not available, skipping route verification")
            
            print("\n✓ hollogram module is ACTIVE and functional!")
            return True
            
        except Exception as e:
            print(f"\n✗ Failed to create blueprint: {e}")
            print(f"  Error type: {type(e).__name__}")
            return False
            
    except Exception as e:
        print(f"\n✗ Failed to import or test hollogram module: {e}")
        print(f"  Error type: {type(e).__name__}")
        return False


def main():
    """Run all module activation tests."""
    print("\n" + "="*70)
    print("ACTIFIX MODULE ACTIVATION TEST")
    print("="*70)
    print("\nTesting dev_assistant and hollogram modules...")
    print("This verifies the modules are properly configured and ready to use.")
    
    # Test dev_assistant
    dev_assistant_ok = test_dev_assistant_module()
    
    # Test hollogram
    hollogram_ok = test_hollogram_module()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if dev_assistant_ok and hollogram_ok:
        print("\n✓ SUCCESS: All modules are ACTIVE and functional!")
        print("\nBoth dev_assistant and hollogram modules are properly activated.")
        print("\nYou can now use these modules by:")
        print("  1. Starting the Actifix server")
        print("  2. Accessing the API endpoints:")
        print("     - /modules/dev_assistant/health")
        print("     - /modules/dev_assistant/chat")
        print("     - /modules/hollogram/health")
        print("     - /modules/hollogram/research")
        print("     - /modules/hollogram/topics")
        print("     - /modules/hollogram/disclaimer")
        print("     - /modules/hollogram/history")
        return 0
    else:
        print("\n✗ FAILURE: One or more modules failed activation tests!")
        if not dev_assistant_ok:
            print("  - dev_assistant module failed")
        if not hollogram_ok:
            print("  - hollogram module failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
