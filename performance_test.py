#!/usr/bin/env python3
"""
Performance test script for the optimized deductive fault simulator.
This script demonstrates the performance improvements made to the simulator.
"""

import time
import sys
import os

# Add the tc_sim directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tc_sim'))

from tc_sim.deductive_fault_simulator import DFSWrapper

def performance_test():
    """Test the performance improvements of the deductive fault simulator."""
    
    # Example circuit file path (you'll need to provide a real circuit file)
    circuit_file = "project2_data/test_case_1_S27_1101101.txt"  # Update this path
    
    if not os.path.exists(circuit_file):
        print(f"Circuit file {circuit_file} not found. Please update the path.")
        return
    
    print("=== Deductive Fault Simulator Performance Test ===")
    print()
    
    # Initialize the wrapper
    print("Initializing DFSWrapper...")
    start_time = time.time()
    dfs_wrapper = DFSWrapper(circuit_file)
    init_time = time.time() - start_time
    print(f"Initialization time: {init_time:.4f} seconds")
    print()
    
    # Test with multiple input patterns
    test_inputs = [
        "1101101",  # Example input pattern
        "0010010",  # Another pattern
        "1101101",  # Repeat to test caching
        "1111111",  # All ones
        "0000000",  # All zeros
    ]
    
    print("Testing fault simulation with multiple input patterns...")
    print(f"Number of test patterns: {len(test_inputs)}")
    print()
    
    total_time = 0
    for i, input_pattern in enumerate(test_inputs):
        print(f"Test {i+1}: Input pattern '{input_pattern}'")
        
        start_time = time.time()
        try:
            detected_faults = dfs_wrapper.deductive_fault_evaluate_circuit_with_normal_input(input_pattern)
            eval_time = time.time() - start_time
            total_time += eval_time
            
            print(f"  Evaluation time: {eval_time:.4f} seconds")
            print(f"  Detected faults: {len(detected_faults)}")
            
            # Show first few faults for verification
            if detected_faults:
                print(f"  Sample faults: {[str(f) for f in detected_faults[:3]]}")
            print()
            
        except Exception as e:
            print(f"  Error: {e}")
            print()
    
    print("=== Performance Summary ===")
    print(f"Total evaluation time: {total_time:.4f} seconds")
    print(f"Average time per pattern: {total_time/len(test_inputs):.4f} seconds")
    print(f"Patterns per second: {len(test_inputs)/total_time:.2f}")
    print()
    
    # Test caching effectiveness
    print("=== Caching Test ===")
    print("Testing repeated input pattern (should be faster due to caching)...")
    
    start_time = time.time()
    dfs_wrapper.deductive_fault_evaluate_circuit_with_normal_input("1101101")
    cached_time = time.time() - start_time
    print(f"Cached evaluation time: {cached_time:.4f} seconds")
    print()
    
    print("Performance test completed!")

if __name__ == "__main__":
    performance_test()


