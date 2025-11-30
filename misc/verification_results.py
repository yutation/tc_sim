#!/usr/bin/env python3
"""
Verification script to compare simulation results with expected outputs
"""

# Expected outputs from the reference image
expected_outputs = {
    "s27": {
        "1110101": "1001",
        "0001010": "0100"
    },
    "s298f_2": {
        "10101010101010101": "00000010101000111000",
        "01011110000000111": "00000000011000001000"
    },
    "s344f_2": {
        "101010101010101011111111": "10101010101010101010101101",
        "010111100000001110000000": "00011110000000100001111100"  # Note: image shows decimal point, treating as binary
    },
    "s349f_2": {
        "101010101010101011111111": "10101010101010101101010101",
        "010111100000001110000000": "00011110000000101011110000"
    }
}

# Our simulation results
our_results = {
    "s27": {
        "1110101": "1001",
        "0001010": "0100",
        "1010101": "1001",
        "0110111": "0001",
        "1010001": "1001"
    },
    "s298f_2": {
        "10101010101010101": "00000010101000111000",
        "01011110000000111": "00000000011000001000",
        "11111000001111000": "00000000001111010010",
        "11100001110001100": "00000000100100100101",
        "01111011110000000": "11111011110000101101"
    },
    "s344f_2": {
        "101010101010101011111111": "10101010101010101010101101",
        "010111100000001110000000": "00011110000000100001111100",
        "111110000011110001111111": "00011100000111011000111010",
        "111000011100011000000000": "00001101111001111111000010",
        "011110111100000001111111": "10011101111000001001000100"
    },
    "s349f_2": {
        "101010101010101011111111": "10101010101010101101010101",
        "010111100000001110000000": "00011110000000101011110000",
        "111110000011110001111111": "00011100000111010001111100",
        "111000011100011000000000": "00001101111001110010001111",
        "011110111100000001111111": "10011101111000001010000100"
    }
}

def verify_results():
    """Compare our results with expected outputs"""
    print("=" * 80)
    print("CIRCUIT SIMULATION VERIFICATION")
    print("=" * 80)
    
    total_tests = 0
    passed_tests = 0
    
    for circuit_name in expected_outputs:
        print(f"\n--- {circuit_name.upper()} CIRCUIT ---")
        circuit_expected = expected_outputs[circuit_name]
        circuit_our = our_results[circuit_name]
        
        circuit_passed = 0
        circuit_total = len(circuit_expected)
        
        for input_str, expected_output in circuit_expected.items():
            total_tests += 1
            our_output = circuit_our.get(input_str, "NOT_FOUND")
            
            if our_output == expected_output:
                print(f"✓ PASS: {input_str} -> {our_output}")
                passed_tests += 1
                circuit_passed += 1
            else:
                print(f"✗ FAIL: {input_str}")
                print(f"    Expected: {expected_output}")
                print(f"    Got:      {our_output}")
                print(f"    Match:    {our_output == expected_output}")
        
        print(f"\n{circuit_name} Summary: {circuit_passed}/{circuit_total} tests passed")
    
    print("\n" + "=" * 80)
    print("OVERALL VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Our simulation results match the expected outputs.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the differences above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    verify_results()
