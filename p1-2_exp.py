from tc_sim.deductive_fault_simulator import DFSWrapper
import os

def run_deductive_simulation():
    """
    Run deductive fault simulation on the provided test cases and save results to file.
    """
    
    # Test cases provided by user
    test_cases = [
        ("S27", "1101101"),
        ("S27", "0101001"), 
        ("S298f_2", "10101011110010101"),
        ("S298f_2", "11101110101110111"),
        ("S344f_2", "101010101010111101111111"),
        ("S344f_2", "111010111010101010001100"),
        ("S349f_2", "101000000010101011111111"),
        ("S349f_2", "111111101010101010001111")
    ]
    
    # Map circuit names to file paths
    circuit_file_map = {
        "S27": "./files/s27.txt",
        "S298f_2": "./files/s298f_2.txt", 
        "S344f_2": "./files/s344f_2.txt",
        "S349f_2": "./files/s349f_2.txt"
    }
    
    for i, (circuit_name, input_pattern) in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {circuit_name}")
        print(f"Input Pattern: {input_pattern}")
        print("-" * 30)
        
        try:
            circuit_file = circuit_file_map[circuit_name]
            
            # Check if circuit file exists
            if not os.path.exists(circuit_file):
                print(f"ERROR: Circuit file {circuit_file} not found!")
                continue
            
            # Create DFSWrapper and run simulation
            dfs_wrapper = DFSWrapper(circuit_file)
            detected_faults = dfs_wrapper.deductive_fault_evaluate_circuit_with_normal_input(input_pattern)
            
            # Save results using the built-in method
            output_file1 = f"test_case_{i}_{circuit_name}_head.txt"
            # dfs_wrapper.save_detected_fault_list(output_file)
            output_file2 = f"test_case_{i}_{circuit_name}_list.txt"
            dfs_wrapper.save_detected_fault_list_v2(output_file1, output_file2)
        except Exception as e:
            print(f"ERROR: {str(e)}")
    
    print("\nAll simulations completed!")

if __name__ == "__main__":
    run_deductive_simulation()
