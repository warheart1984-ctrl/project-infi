#!/usr/bin/env python3
"""
Test ULX Integration with Nova Runtime
Verifies ULX constitutional programming integration with Nova Cortex
"""

import sys
sys.path.insert(0, 'E:\\')

from prime_architect_integration import NovaCortexIntegration, SAMPLE_CONSTITUTION
from ulx import Interpreter, Parser, lex


def test_ulx_parsing():
    """Test ULX constitution parsing"""
    print("Testing ULX Constitution Parsing...")
    
    try:
        lexer = Lexer(SAMPLE_CONSTITUTION)
        tokens = lexer.lex()
        print(f"✓ Lexed {len(tokens)} tokens")
        
        parser = Parser(tokens)
        ast = parser.parse_program()
        print(f"✓ Parsed AST with {len(ast)} nodes")
        
        return True
    except Exception as e:
        print(f"✗ Parsing failed: {e}")
        return False


def test_ulx_interpreter():
    """Test ULX interpreter execution"""
    print("\nTesting ULX Interpreter...")
    
    try:
        lexer = Lexer(SAMPLE_CONSTITUTION)
        tokens = lexer.lex()
        parser = Parser(tokens)
        ast = parser.parse_program()
        
        interpreter = Interpreter()
        interpreter.load(ast)
        
        # Test constitutional validation function
        result = interpreter.call_function("constitutional_governance", "validate_constitution", [])
        print(f"✓ Interpreter executed validate_constitution: {result}")
        
        return True
    except Exception as e:
        print(f"✗ Interpreter failed: {e}")
        return False


def test_nova_integration():
    """Test Nova Cortex integration with ULX"""
    print("\nTesting Nova Cortex Integration...")
    
    try:
        nova = NovaCortexIntegration()
        
        # Bootstrap with ULX constitution
        nova.bootstrap_layer0(SAMPLE_CONSTITUTION)
        print("✓ Nova Cortex bootstrapped with ULX constitution")
        
        # Integrate with Nova runtime
        nova.integrate_nova_cortex()
        print("✓ Nova Cortex integrated with Nova runtime")
        
        # Activate dual-layer runtime
        nova.activate_dual_layer_runtime()
        print("✓ Dual-layer runtime activated")
        
        # Test AI session validation
        test_header = {
            "SOVEREIGN-CONTEXT": "v1.0.0",
            "UCDD": "S-007 COMPLIANT",
            "LAYER": "5",
            "COMPONENT": "nova-cortex",
            "TRACE-ID": "TM-NOVA-001",
            "AUTHORITY": "PRIME-ARCHITECT-CONSTITUTIONAL"
        }
        
        valid, msg = nova.validate_ai_session(test_header)
        print(f"✓ AI session validation: {valid} - {msg}")
        
        return True
    except Exception as e:
        print(f"✗ Nova integration failed: {e}")
        return False


def test_constitutional_validation():
    """Test constitutional validation through Nova"""
    print("\nTesting Constitutional Validation...")
    
    try:
        nova = NovaCortexIntegration()
        nova.bootstrap_layer0(SAMPLE_CONSTITUTION)
        
        # Test a simple query
        test_query = "Validate constitutional integrity"
        result = nova.process_query(test_query)
        print(f"✓ Query processed: {result}")
        
        # Validate against constitutions
        validation = nova.validate_against_constitutions(result)
        print(f"✓ Constitutional validation: {validation}")
        
        return True
    except Exception as e:
        print(f"✗ Constitutional validation failed: {e}")
        return False


def main():
    """Run all ULX-Nova integration tests"""
    print("="*60)
    print("ULX-NOVA INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        ("ULX Parsing", test_ulx_parsing),
        ("ULX Interpreter", test_ulx_interpreter),
        ("Nova Integration", test_nova_integration),
        ("Constitutional Validation", test_constitutional_validation),
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    for test_name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {test_name}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
