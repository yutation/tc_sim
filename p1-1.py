import sys
import os


from tc_sim.circuit import CircuitWrapper
from tc_sim.gate import NodeValue

# Define all circuit files
circuit_files = [
    "./files/s27.txt",
    "./files/s298f_2.txt", 
    "./files/s344f_2.txt",
    "./files/s349f_2.txt"
]

# Test inputs for each circuit
test_cases = {
    "s27": [
        "1110101",
        "0001010", 
        "1010101",
        "0110111",
        "1010001"
    ],
    "s298f_2": [
        "10101010101010101",
        "01011110000000111",
        "11111000001111000",
        "11100001110001100",
        "01111011110000000"
    ],
    "s344f_2": [
        "101010101010101011111111",
        "010111100000001110000000",
        "111110000011110001111111",
        "111000011100011000000000",
        "011110111100000001111111"
    ],
    "s349f_2": [
        "101010101010101011111111",
        "010111100000001110000000",
        "111110000011110001111111",
        "111000011100011000000000",
        "011110111100000001111111"
    ]
}

def run_circuit_simulation():
    """Run simulation for all circuits with their test cases"""
    
    # Build all circuits
    print("=" * 60)
    print("BUILDING CIRCUITS")
    print("=" * 60)
    
    wrappers = {}
    for circuit_file in circuit_files:
        circuit_name = circuit_file.split('/')[-1].split('.')[0]
        print(f"Building circuit: {circuit_file}")
        wrapper = CircuitWrapper(circuit_file)
        wrapper.build_circuit()
        wrappers[circuit_name] = wrapper
        print(f"✓ Successfully built circuit: {circuit_name}")
    
    print(f"\nBuilt {len(wrappers)} circuits successfully!")
    
    # Run simulations
    print("\n" + "=" * 60)
    print("RUNNING SIMULATIONS")
    print("=" * 60)
    
    for circuit_name, wrapper in wrappers.items():
        print(f"\n--- Testing {circuit_name} ---")
        print(f"Input ports: {wrapper.circuit.input_port_names}")
        print(f"Output ports: {wrapper.circuit.output_port_names}")
        
        if circuit_name in test_cases:
            test_inputs = test_cases[circuit_name]
            print(f"Running {len(test_inputs)} test cases...")
            
            for i, test_input in enumerate(test_inputs, 1):
                try:
                    output = wrapper.evaluate_circuit_with_normal_input(test_input)
                    print(f"  Test {i}: {test_input} -> {output}")
                except Exception as e:
                    print(f"  Test {i}: {test_input} -> ERROR: {e}")
        else:
            print(f"No test cases defined for {circuit_name}")

if __name__ == "__main__":
    run_circuit_simulation()