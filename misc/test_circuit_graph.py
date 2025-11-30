#!/usr/bin/env python3
"""
Test script to demonstrate circuit graph generation functionality.
This script creates a simple circuit and generates its graph visualization.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tc_sim'))

from tc_sim.circuit import Circuit, CircuitWrapper
from tc_sim.gate import GateType

def create_simple_circuit():
    """Create a simple circuit for testing graph generation"""
    circuit = Circuit()
    
    # Add input gates
    circuit.add_a_gate_with_wires("input_a", GateType.INPUT, [], "a")
    circuit.add_a_gate_with_wires("input_b", GateType.INPUT, [], "b")
    circuit.add_a_gate_with_wires("input_c", GateType.INPUT, [], "c")
    
    # Add logic gates
    circuit.add_a_gate_with_wires("and1", GateType.AND, ["a", "b"], "ab")
    circuit.add_a_gate_with_wires("or1", GateType.OR, ["ab", "c"], "abc")
    circuit.add_a_gate_with_wires("not1", GateType.NOT, ["abc"], "result")
    
    # Add output gate
    circuit.add_a_gate_with_wires("output", GateType.OUTPUT, ["result"], None)
    
    # Connect all gates
    circuit.connect_gates()
    
    return circuit

def test_graph_generation():
    """Test the graph generation functionality"""
    print("Creating a simple circuit...")
    circuit = create_simple_circuit()
    
    print(f"Circuit has {len(circuit.gates)} gates and {len(circuit.wires)} wires")
    print(f"Input ports: {circuit.input_port_names}")
    print(f"Output ports: {circuit.output_port_names}")
    
    print("\nGenerating graph visualization...")
    try:
        # Generate graph with wires shown
        G = circuit.generate_graph(show_wires=True, layout='hierarchical', figsize=(10, 6))
        print("Graph generated successfully!")
        print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        
        # Export to DOT format
        print("\nExporting to DOT format...")
        dot_content = circuit.export_to_dot("circuit_graph.dot", show_wires=True)
        print("DOT file exported as 'circuit_graph.dot'")
        
        # Also create a version without wires
        print("\nGenerating simplified graph (without wires)...")
        G_simple = circuit.generate_graph(show_wires=False, layout='spring', figsize=(8, 6))
        
    except ImportError as e:
        print(f"Error: Missing required dependencies: {e}")
        print("Please install matplotlib and networkx:")
        print("pip install matplotlib networkx")
        return False
    
    return True

def test_circuit_from_file():
    """Test graph generation from a circuit file"""
    # Create a sample circuit file
    circuit_file_content = """INPUT a b c -1
OUTPUT result -1
AND a b ab
OR ab c abc
NOT abc result
"""
    
    with open("sample_circuit.txt", "w") as f:
        f.write(circuit_file_content)
    
    print("\nTesting circuit loading from file...")
    wrapper = CircuitWrapper("sample_circuit.txt")
    wrapper.build_circuit()
    
    print(f"Loaded circuit has {len(wrapper.circuit.gates)} gates")
    
    try:
        # Generate graph
        G = wrapper.circuit.generate_graph(show_wires=True, layout='hierarchical')
        print("Graph generated from file successfully!")
        
        # Export DOT
        wrapper.circuit.export_to_dot("file_circuit_graph.dot")
        print("DOT file exported as 'file_circuit_graph.dot'")
        
    except ImportError as e:
        print(f"Error: Missing required dependencies: {e}")
        return False
    
    # Clean up
    os.remove("sample_circuit.txt")
    return True

if __name__ == "__main__":
    print("=== Circuit Graph Generation Test ===")
    
    # Test 1: Create circuit programmatically
    success1 = test_graph_generation()
    
    # Test 2: Load circuit from file
    success2 = test_circuit_from_file()
    
    if success1 and success2:
        print("\n✅ All tests completed successfully!")
        print("\nGenerated files:")
        print("- circuit_graph.dot (programmatic circuit)")
        print("- file_circuit_graph.dot (file-loaded circuit)")
        print("\nYou can visualize these DOT files using Graphviz:")
        print("dot -Tpng circuit_graph.dot -o circuit_graph.png")
    else:
        print("\n❌ Some tests failed. Please install required dependencies.")
