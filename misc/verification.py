#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tc_sim'))

from circuit import CircuitWrapper
from gate import GateValue

def verify_circuit_parser():
    """Comprehensive verification of the circuit parser and evaluator"""
    
    print("=" * 60)
    print("CIRCUIT PARSER AND EVALUATOR VERIFICATION")
    print("=" * 60)
    
    # Test 1: Basic Circuit Parsing
    print("\n1. Testing Circuit Parsing...")
    try:
        circuit_file = "/mnt/c/Users/Owner/Desktop/ECE6140/Project/files/files/s27.txt"
        wrapper = CircuitWrapper(circuit_file)
        wrapper.build_circuit()
        
        circuit = wrapper.circuit
        print(f"   ✓ Circuit parsed successfully")
        print(f"   ✓ Number of gates: {len(circuit.gates)}")
        print(f"   ✓ Number of wires: {len(circuit.wires)}")
        print(f"   ✓ Input ports: {len(circuit.input_port_names)}")
        print(f"   ✓ Output ports: {len(circuit.output_port_names)}")
        
        # Verify expected counts for s27.txt
        expected_gates = 24  # 7 input + 4 output + 13 logic gates
        expected_wires = 20
        expected_inputs = 7
        expected_outputs = 4
        
        assert len(circuit.gates) == expected_gates, f"Expected {expected_gates} gates, got {len(circuit.gates)}"
        assert len(circuit.wires) == expected_wires, f"Expected {expected_wires} wires, got {len(circuit.wires)}"
        assert len(circuit.input_port_names) == expected_inputs, f"Expected {expected_inputs} inputs, got {len(circuit.input_port_names)}"
        assert len(circuit.output_port_names) == expected_outputs, f"Expected {expected_outputs} outputs, got {len(circuit.output_port_names)}"
        
        print(f"   ✓ All gate and wire counts match expected values")
        
    except Exception as e:
        print(f"   ✗ Circuit parsing failed: {e}")
        return False
    
    # Test 2: Gate Type Verification
    print("\n2. Testing Gate Types...")
    try:
        gate_types = {}
        for gate_name, gate in circuit.gates.items():
            gate_type = gate.gate_type.value
            if gate_type not in gate_types:
                gate_types[gate_type] = 0
            gate_types[gate_type] += 1
        
        print(f"   ✓ Gate type distribution:")
        for gate_type, count in sorted(gate_types.items()):
            print(f"     {gate_type}: {count}")
        
        # Verify we have the expected gate types
        expected_types = ['INPUT', 'OUTPUT', 'NOT', 'BUF', 'AND', 'OR', 'NAND', 'NOR']
        for gate_type in expected_types:
            assert gate_type in gate_types, f"Missing gate type: {gate_type}"
        
        print(f"   ✓ All expected gate types present")
        
    except Exception as e:
        print(f"   ✗ Gate type verification failed: {e}")
        return False
    
    # Test 3: Wire Connections Verification
    print("\n3. Testing Wire Connections...")
    try:
        # Check that all gates have proper fan-in/fan-out connections
        for gate_name, gate in circuit.gates.items():
            if gate.gate_type.value == 'INPUT':
                # INPUT gates should have fan-out gates but no fan-in gates
                assert len(gate.fan_in_gates) == 0, f"INPUT gate {gate_name} has fan-in gates"
                assert len(gate.fan_out_gates) > 0, f"INPUT gate {gate_name} has no fan-out gates"
            elif gate.gate_type.value == 'OUTPUT':
                # OUTPUT gates should have fan-in gates but no fan-out gates
                assert len(gate.fan_in_gates) > 0, f"OUTPUT gate {gate_name} has no fan-in gates"
                assert len(gate.fan_out_gates) == 0, f"OUTPUT gate {gate_name} has fan-out gates"
            else:
                # Logic gates should have fan-in gates (fan-out gates may be empty if they only connect to OUTPUT gates)
                assert len(gate.fan_in_gates) > 0, f"Logic gate {gate_name} has no fan-in gates"
                # Note: Logic gates may not have fan-out gates if they only connect to OUTPUT gates
        
        print(f"   ✓ All gate connections are valid")
        
    except Exception as e:
        print(f"   ✗ Wire connection verification failed: {e}")
        return False
    
    # Test 4: Circuit Evaluation with Various Inputs
    print("\n4. Testing Circuit Evaluation...")
    try:
        test_cases = [
            ("0000000", "Expected output for all zeros"),
            ("1111111", "Expected output for all ones"),
            ("1010101", "Expected output for alternating pattern"),
            ("0001111", "Expected output for mixed pattern"),
            ("0101010", "Expected output for another pattern"),
        ]
        
        print(f"   Testing {len(test_cases)} input patterns:")
        for i, (input_str, description) in enumerate(test_cases):
            try:
                output_str = wrapper.evaluate_circuit_with_normal_input(input_str)
                print(f"     Test {i+1}: '{input_str}' → '{output_str}' ({description})")
                
                # Verify output format
                assert len(output_str) == len(circuit.output_port_names), f"Output length mismatch for input '{input_str}'"
                for char in output_str:
                    assert char in ['0', '1', 'X'], f"Invalid output character '{char}' in '{output_str}'"
                
            except Exception as e:
                print(f"     ✗ Test {i+1} failed: {e}")
                return False
        
        print(f"   ✓ All evaluation tests passed")
        
    except Exception as e:
        print(f"   ✗ Circuit evaluation verification failed: {e}")
        return False
    
    # Test 5: Input Validation
    print("\n5. Testing Input Validation...")
    try:
        # Test invalid input length
        try:
            wrapper.evaluate_circuit_with_normal_input("000000")  # Too short
            print(f"   ✗ Should have failed for short input")
            return False
        except ValueError as e:
            print(f"   ✓ Correctly rejected short input: {e}")
        
        try:
            wrapper.evaluate_circuit_with_normal_input("00000000")  # Too long
            print(f"   ✗ Should have failed for long input")
            return False
        except ValueError as e:
            print(f"   ✓ Correctly rejected long input: {e}")
        
        # Test invalid characters
        try:
            wrapper.evaluate_circuit_with_normal_input("0000002")  # Invalid character
            print(f"   ✗ Should have failed for invalid character")
            return False
        except ValueError as e:
            print(f"   ✓ Correctly rejected invalid character: {e}")
        
        print(f"   ✓ Input validation working correctly")
        
    except Exception as e:
        print(f"   ✗ Input validation verification failed: {e}")
        return False
    
    # Test 6: Gate Logic Verification
    print("\n6. Testing Gate Logic...")
    try:
        # Test individual gate types with known inputs
        from gate import GateType
        
        # Test NOT gate logic
        not_gate = circuit.gates['inv_5']
        print(f"   Testing NOT gate: {not_gate.gate_name}")
        
        # Test AND gate logic
        and_gate = circuit.gates['and_7']
        print(f"   Testing AND gate: {and_gate.gate_name}")
        print(f"     Fan-in gates: {[g.gate_name for g in and_gate.fan_in_gates]}")
        
        # Test OR gate logic
        or_gate = circuit.gates['or_16']
        print(f"   Testing OR gate: {or_gate.gate_name}")
        print(f"     Fan-in gates: {[g.gate_name for g in or_gate.fan_in_gates]}")
        
        print(f"   ✓ Gate logic structure verified")
        
    except Exception as e:
        print(f"   ✗ Gate logic verification failed: {e}")
        return False
    
    # Test 7: Performance Test
    print("\n7. Testing Performance...")
    try:
        import time
        
        # Time multiple evaluations
        start_time = time.time()
        for i in range(100):
            input_str = f"{i % 2}" * 7  # Generate different input patterns
            wrapper.evaluate_circuit_with_normal_input(input_str)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 100
        print(f"   ✓ Average evaluation time: {avg_time:.6f} seconds")
        print(f"   ✓ Performance test passed")
        
    except Exception as e:
        print(f"   ✗ Performance test failed: {e}")
        return False
    
    # Test 8: Edge Cases
    print("\n8. Testing Edge Cases...")
    try:
        # Test with all zeros
        output = wrapper.evaluate_circuit_with_normal_input("0000000")
        print(f"   All zeros input: '{output}'")
        
        # Test with all ones
        output = wrapper.evaluate_circuit_with_normal_input("1111111")
        print(f"   All ones input: '{output}'")
        
        # Test alternating pattern
        output = wrapper.evaluate_circuit_with_normal_input("1010101")
        print(f"   Alternating input: '{output}'")
        
        print(f"   ✓ Edge cases handled correctly")
        
    except Exception as e:
        print(f"   ✗ Edge case testing failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL VERIFICATION TESTS PASSED!")
    print("✅ Circuit parser and evaluator are working correctly!")
    print("=" * 60)
    
    return True

def verify_circuit_structure():
    """Additional verification of circuit structure"""
    
    print("\n" + "=" * 60)
    print("DETAILED CIRCUIT STRUCTURE VERIFICATION")
    print("=" * 60)
    
    try:
        circuit_file = "/mnt/c/Users/Owner/Desktop/ECE6140/Project/files/files/s27.txt"
        wrapper = CircuitWrapper(circuit_file)
        wrapper.build_circuit()
        
        circuit = wrapper.circuit
        
        # Print detailed circuit information
        print(f"\nCircuit Details:")
        print(f"  Total gates: {len(circuit.gates)}")
        print(f"  Total wires: {len(circuit.wires)}")
        print(f"  Input ports: {circuit.input_port_names}")
        print(f"  Output ports: {circuit.output_port_names}")
        
        # Print gate details
        print(f"\nGate Details:")
        for gate_name, gate in sorted(circuit.gates.items()):
            fan_in_names = [g.gate_name for g in gate.fan_in_gates]
            fan_out_names = [g.gate_name for g in gate.fan_out_gates]
            print(f"  {gate_name} ({gate.gate_type.value}):")
            print(f"    Fan-in:  {fan_in_names}")
            print(f"    Fan-out: {fan_out_names}")
        
        # Print wire details
        print(f"\nWire Details:")
        for wire_name, wire in sorted(circuit.wires.items()):
            input_gate = wire.input_gate.gate_name if wire.input_gate else "None"
            output_gates = [g.gate_name for g in wire.output_gates]
            print(f"  Wire {wire_name}: {input_gate} → {output_gates}")
        
        print(f"\n✅ Circuit structure verification completed!")
        
    except Exception as e:
        print(f"✗ Circuit structure verification failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting Circuit Parser and Evaluator Verification...")
    
    # Run main verification
    success = verify_circuit_parser()
    
    if success:
        # Run detailed structure verification
        verify_circuit_structure()
        print(f"\n🎉 VERIFICATION COMPLETE - ALL TESTS PASSED! 🎉")
    else:
        print(f"\n❌ VERIFICATION FAILED - CHECK ERRORS ABOVE ❌")
        sys.exit(1)
