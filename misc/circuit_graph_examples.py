#!/usr/bin/env python3
"""
Comprehensive examples demonstrating circuit graph generation functionality.
This script creates various types of circuits and generates their graph visualizations.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tc_sim'))

from tc_sim.circuit import Circuit, CircuitWrapper
from tc_sim.gate import GateType

def example_1_simple_and_or():
    """Example 1: Simple AND-OR circuit"""
    print("=== Example 1: Simple AND-OR Circuit ===")
    circuit = Circuit()
    
    # Inputs
    circuit.add_a_gate_with_wires("input_x", GateType.INPUT, [], "x")
    circuit.add_a_gate_with_wires("input_y", GateType.INPUT, [], "y")
    circuit.add_a_gate_with_wires("input_z", GateType.INPUT, [], "z")
    
    # Logic: (x AND y) OR z
    circuit.add_a_gate_with_wires("and1", GateType.AND, ["x", "y"], "xy")
    circuit.add_a_gate_with_wires("or1", GateType.OR, ["xy", "z"], "result")
    
    # Output
    circuit.add_a_gate_with_wires("output", GateType.OUTPUT, ["result"], None)
    
    circuit.connect_gates()
    
    print(f"Gates: {len(circuit.gates)}, Wires: {len(circuit.wires)}")
    print("Logic: (x AND y) OR z")
    
    try:
        circuit.generate_graph(show_wires=True, layout='hierarchical', figsize=(10, 6))
        circuit.export_to_dot("example1_and_or.dot")
        print("✅ Graph generated and saved as 'example1_and_or.dot'")
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")
    
    return circuit

def example_2_xor_circuit():
    """Example 2: XOR circuit using basic gates"""
    print("\n=== Example 2: XOR Circuit ===")
    circuit = Circuit()
    
    # Inputs
    circuit.add_a_gate_with_wires("input_a", GateType.INPUT, [], "a")
    circuit.add_a_gate_with_wires("input_b", GateType.INPUT, [], "b")
    
    # XOR implementation: (a AND NOT b) OR (NOT a AND b)
    circuit.add_a_gate_with_wires("not_a", GateType.NOT, ["a"], "not_a")
    circuit.add_a_gate_with_wires("not_b", GateType.NOT, ["b"], "not_b")
    circuit.add_a_gate_with_wires("and1", GateType.AND, ["a", "not_b"], "a_not_b")
    circuit.add_a_gate_with_wires("and2", GateType.AND, ["not_a", "b"], "not_a_b")
    circuit.add_a_gate_with_wires("or1", GateType.OR, ["a_not_b", "not_a_b"], "xor_result")
    
    # Output
    circuit.add_a_gate_with_wires("output", GateType.OUTPUT, ["xor_result"], None)
    
    circuit.connect_gates()
    
    print(f"Gates: {len(circuit.gates)}, Wires: {len(circuit.wires)}")
    print("Logic: A XOR B using basic gates")
    
    try:
        circuit.generate_graph(show_wires=True, layout='hierarchical', figsize=(12, 8))
        circuit.export_to_dot("example2_xor.dot")
        print("✅ Graph generated and saved as 'example2_xor.dot'")
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")
    
    return circuit

def example_3_full_adder():
    """Example 3: Full Adder circuit"""
    print("\n=== Example 3: Full Adder Circuit ===")
    circuit = Circuit()
    
    # Inputs: A, B, Cin
    circuit.add_a_gate_with_wires("input_a", GateType.INPUT, [], "a")
    circuit.add_a_gate_with_wires("input_b", GateType.INPUT, [], "b")
    circuit.add_a_gate_with_wires("input_cin", GateType.INPUT, [], "cin")
    
    # Sum = A XOR B XOR Cin
    circuit.add_a_gate_with_wires("xor1", GateType.XOR, ["a", "b"], "a_xor_b")
    circuit.add_a_gate_with_wires("xor2", GateType.XOR, ["a_xor_b", "cin"], "sum")
    
    # Cout = (A AND B) OR (Cin AND (A XOR B))
    circuit.add_a_gate_with_wires("and1", GateType.AND, ["a", "b"], "a_and_b")
    circuit.add_a_gate_with_wires("and2", GateType.AND, ["cin", "a_xor_b"], "cin_and_axorb")
    circuit.add_a_gate_with_wires("or1", GateType.OR, ["a_and_b", "cin_and_axorb"], "cout")
    
    # Outputs
    circuit.add_a_gate_with_wires("output_sum", GateType.OUTPUT, ["sum"], None)
    circuit.add_a_gate_with_wires("output_cout", GateType.OUTPUT, ["cout"], None)
    
    circuit.connect_gates()
    
    print(f"Gates: {len(circuit.gates)}, Wires: {len(circuit.wires)}")
    print("Logic: Full Adder (A + B + Cin = Sum, Cout)")
    
    try:
        circuit.generate_graph(show_wires=True, layout='hierarchical', figsize=(14, 10))
        circuit.export_to_dot("example3_full_adder.dot")
        print("✅ Graph generated and saved as 'example3_full_adder.dot'")
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")
    
    return circuit

def example_4_complex_logic():
    """Example 4: Complex logic circuit with multiple outputs"""
    print("\n=== Example 4: Complex Logic Circuit ===")
    circuit = Circuit()
    
    # Inputs
    circuit.add_a_gate_with_wires("input_p", GateType.INPUT, [], "p")
    circuit.add_a_gate_with_wires("input_q", GateType.INPUT, [], "q")
    circuit.add_a_gate_with_wires("input_r", GateType.INPUT, [], "r")
    circuit.add_a_gate_with_wires("input_s", GateType.INPUT, [], "s")
    
    # Complex logic: F1 = (P AND Q) OR (R AND S), F2 = (P OR Q) AND (R OR S)
    circuit.add_a_gate_with_wires("and1", GateType.AND, ["p", "q"], "p_and_q")
    circuit.add_a_gate_with_wires("and2", GateType.AND, ["r", "s"], "r_and_s")
    circuit.add_a_gate_with_wires("or1", GateType.OR, ["p_and_q", "r_and_s"], "f1")
    
    circuit.add_a_gate_with_wires("or2", GateType.OR, ["p", "q"], "p_or_q")
    circuit.add_a_gate_with_wires("or3", GateType.OR, ["r", "s"], "r_or_s")
    circuit.add_a_gate_with_wires("and3", GateType.AND, ["p_or_q", "r_or_s"], "f2")
    
    # Outputs
    circuit.add_a_gate_with_wires("output_f1", GateType.OUTPUT, ["f1"], None)
    circuit.add_a_gate_with_wires("output_f2", GateType.OUTPUT, ["f2"], None)
    
    circuit.connect_gates()
    
    print(f"Gates: {len(circuit.gates)}, Wires: {len(circuit.wires)}")
    print("Logic: F1 = (P AND Q) OR (R AND S), F2 = (P OR Q) AND (R OR S)")
    
    try:
        circuit.generate_graph(show_wires=True, layout='spring', figsize=(12, 8))
        circuit.export_to_dot("example4_complex.dot")
        print("✅ Graph generated and saved as 'example4_complex.dot'")
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")
    
    return circuit

def example_5_from_file():
    """Example 5: Load circuit from file and visualize"""
    print("\n=== Example 5: Circuit from File ===")
    
    # Create a sample circuit file
    circuit_file_content = """INPUT a b c d -1
OUTPUT f1 f2 -1
AND a b ab
AND c d cd
OR ab cd f1
OR a b a_or_b
OR c d c_or_d
AND a_or_b c_or_d f2
"""
    
    with open("sample_circuit.txt", "w") as f:
        f.write(circuit_file_content)
    
    try:
        wrapper = CircuitWrapper("sample_circuit.txt")
        wrapper.build_circuit()
        
        print(f"Loaded circuit: {len(wrapper.circuit.gates)} gates, {len(wrapper.circuit.wires)} wires")
        print("Inputs:", wrapper.circuit.input_port_names)
        print("Outputs:", wrapper.circuit.output_port_names)
        
        # Test evaluation
        result = wrapper.evaluate_circuit_with_normal_input("1010")
        print(f"Test evaluation with input '1010': output = '{result}'")
        
        # Generate graph
        wrapper.circuit.generate_graph(show_wires=True, layout='hierarchical', figsize=(12, 8))
        wrapper.circuit.export_to_dot("example5_from_file.dot")
        print("✅ Graph generated and saved as 'example5_from_file.dot'")
        
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up
        if os.path.exists("sample_circuit.txt"):
            os.remove("sample_circuit.txt")

def example_6_different_layouts():
    """Example 6: Same circuit with different layouts"""
    print("\n=== Example 6: Different Layout Styles ===")
    circuit = Circuit()
    
    # Create a simple circuit
    circuit.add_a_gate_with_wires("input_x", GateType.INPUT, [], "x")
    circuit.add_a_gate_with_wires("input_y", GateType.INPUT, [], "y")
    circuit.add_a_gate_with_wires("input_z", GateType.INPUT, [], "z")
    
    circuit.add_a_gate_with_wires("and1", GateType.AND, ["x", "y"], "xy")
    circuit.add_a_gate_with_wires("not1", GateType.NOT, ["xy"], "not_xy")
    circuit.add_a_gate_with_wires("or1", GateType.OR, ["not_xy", "z"], "result")
    
    circuit.add_a_gate_with_wires("output", GateType.OUTPUT, ["result"], None)
    circuit.connect_gates()
    
    layouts = ['hierarchical', 'spring', 'circular']
    
    try:
        for i, layout in enumerate(layouts, 1):
            print(f"  Generating {layout} layout...")
            circuit.generate_graph(
                show_wires=True, 
                layout=layout, 
                figsize=(8, 6),
                save_path=f"example6_{layout}.png"
            )
            circuit.export_to_dot(f"example6_{layout}.dot")
        
        print("✅ All layout styles generated!")
        print("Files created:")
        for layout in layouts:
            print(f"  - example6_{layout}.png (image)")
            print(f"  - example6_{layout}.dot (DOT format)")
            
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")

def example_7_without_wires():
    """Example 7: Simplified view without wire nodes"""
    print("\n=== Example 7: Simplified View (No Wires) ===")
    circuit = Circuit()
    
    # Create a circuit with multiple gates
    circuit.add_a_gate_with_wires("input_a", GateType.INPUT, [], "a")
    circuit.add_a_gate_with_wires("input_b", GateType.INPUT, [], "b")
    circuit.add_a_gate_with_wires("input_c", GateType.INPUT, [], "c")
    
    circuit.add_a_gate_with_wires("nand1", GateType.NAND, ["a", "b"], "nand_ab")
    circuit.add_a_gate_with_wires("nor1", GateType.NOR, ["b", "c"], "nor_bc")
    circuit.add_a_gate_with_wires("xor1", GateType.XOR, ["nand_ab", "nor_bc"], "xor_result")
    circuit.add_a_gate_with_wires("xnor1", GateType.XNOR, ["xor_result", "c"], "final")
    
    circuit.add_a_gate_with_wires("output", GateType.OUTPUT, ["final"], None)
    circuit.connect_gates()
    
    print(f"Gates: {len(circuit.gates)}, Wires: {len(circuit.wires)}")
    print("Logic: Complex combination of NAND, NOR, XOR, XNOR")
    
    try:
        # Show both versions
        print("  Generating with wires...")
        circuit.generate_graph(show_wires=True, layout='hierarchical', figsize=(10, 6))
        circuit.export_to_dot("example7_with_wires.dot")
        
        print("  Generating without wires...")
        circuit.generate_graph(show_wires=False, layout='spring', figsize=(10, 6))
        circuit.export_to_dot("example7_without_wires.dot")
        
        print("✅ Both versions generated!")
        print("Files: example7_with_wires.dot, example7_without_wires.dot")
        
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")

def main():
    """Run all examples"""
    print("🔌 Circuit Graph Generation Examples")
    print("=" * 50)
    
    # Check dependencies
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
        print("✅ Dependencies found - generating visualizations...")
    except ImportError:
        print("❌ Missing dependencies. Please install:")
        print("   pip install matplotlib networkx")
        print("\nGenerating DOT files only...")
    
    # Run examples
    examples = [
        example_1_simple_and_or,
        example_2_xor_circuit,
        example_3_full_adder,
        example_4_complex_logic,
        example_5_from_file,
        example_6_different_layouts,
        example_7_without_wires
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"❌ Error in {example_func.__name__}: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 All examples completed!")
    print("\nGenerated files:")
    print("📁 DOT files (for Graphviz):")
    print("   - example1_and_or.dot")
    print("   - example2_xor.dot") 
    print("   - example3_full_adder.dot")
    print("   - example4_complex.dot")
    print("   - example5_from_file.dot")
    print("   - example6_*.dot (3 layouts)")
    print("   - example7_*.dot (with/without wires)")
    print("\n📁 PNG files (if matplotlib available):")
    print("   - example6_*.png (3 layout styles)")
    print("\n🔧 To convert DOT to images:")
    print("   dot -Tpng example1_and_or.dot -o example1_and_or.png")
    print("   dot -Tsvg example2_xor.dot -o example2_xor.svg")

if __name__ == "__main__":
    main()
