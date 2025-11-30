#!/usr/bin/env python3
"""
Test script demonstrating the improved circuit graph generation
with proper gate shapes and no wire nodes.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tc_sim'))

from tc_sim.circuit import Circuit
from tc_sim.gate import GateType

def test_improved_graphs():
    """Test the improved circuit graph generation"""
    print("🔌 Improved Circuit Graph Generation Test")
    print("=" * 60)
    
    # Test 1: Simple AND-OR circuit
    print("\n=== Test 1: Simple AND-OR Circuit ===")
    circuit1 = Circuit()
    
    # Inputs
    circuit1.add_a_gate_with_wires("input_x", GateType.INPUT, [], "x")
    circuit1.add_a_gate_with_wires("input_y", GateType.INPUT, [], "y")
    circuit1.add_a_gate_with_wires("input_z", GateType.INPUT, [], "z")
    
    # Logic: (x AND y) OR z
    circuit1.add_a_gate_with_wires("and1", GateType.AND, ["x", "y"], "xy")
    circuit1.add_a_gate_with_wires("or1", GateType.OR, ["xy", "z"], "result")
    
    # Output
    circuit1.add_a_gate_with_wires("output", GateType.OUTPUT, ["result"], None)
    
    circuit1.connect_gates()
    
    print(f"Gates: {len(circuit1.gates)}, Wires: {len(circuit1.wires)}")
    print("Logic: (x AND y) OR z")
    
    try:
        # Generate improved graph
        circuit1.generate_graph(layout='hierarchical', figsize=(10, 6), save_path='improved_circuit1.png')
        circuit1.export_to_dot('improved_circuit1.dot')
        print("✅ Improved graph generated!")
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")
    
    # Test 2: XOR circuit with different gate types
    print("\n=== Test 2: XOR Circuit with Various Gate Types ===")
    circuit2 = Circuit()
    
    # Inputs
    circuit2.add_a_gate_with_wires("input_a", GateType.INPUT, [], "a")
    circuit2.add_a_gate_with_wires("input_b", GateType.INPUT, [], "b")
    
    # XOR implementation using different gate types
    circuit2.add_a_gate_with_wires("not_a", GateType.NOT, ["a"], "not_a")
    circuit2.add_a_gate_with_wires("not_b", GateType.NOT, ["b"], "not_b")
    circuit2.add_a_gate_with_wires("and1", GateType.AND, ["a", "not_b"], "a_not_b")
    circuit2.add_a_gate_with_wires("and2", GateType.AND, ["not_a", "b"], "not_a_b")
    circuit2.add_a_gate_with_wires("or1", GateType.OR, ["a_not_b", "not_a_b"], "xor_result")
    
    # Output
    circuit2.add_a_gate_with_wires("output", GateType.OUTPUT, ["xor_result"], None)
    
    circuit2.connect_gates()
    
    print(f"Gates: {len(circuit2.gates)}, Wires: {len(circuit2.wires)}")
    print("Logic: A XOR B using NOT, AND, OR gates")
    
    try:
        circuit2.generate_graph(layout='hierarchical', figsize=(12, 8), save_path='improved_circuit2.png')
        circuit2.export_to_dot('improved_circuit2.dot')
        print("✅ Improved graph generated!")
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")
    
    # Test 3: Full Adder with all gate types
    print("\n=== Test 3: Full Adder with All Gate Types ===")
    circuit3 = Circuit()
    
    # Inputs
    circuit3.add_a_gate_with_wires("input_a", GateType.INPUT, [], "a")
    circuit3.add_a_gate_with_wires("input_b", GateType.INPUT, [], "b")
    circuit3.add_a_gate_with_wires("input_cin", GateType.INPUT, [], "cin")
    
    # Sum = A XOR B XOR Cin
    circuit3.add_a_gate_with_wires("xor1", GateType.XOR, ["a", "b"], "a_xor_b")
    circuit3.add_a_gate_with_wires("xor2", GateType.XOR, ["a_xor_b", "cin"], "sum")
    
    # Cout = (A AND B) OR (Cin AND (A XOR B))
    circuit3.add_a_gate_with_wires("and1", GateType.AND, ["a", "b"], "a_and_b")
    circuit3.add_a_gate_with_wires("and2", GateType.AND, ["cin", "a_xor_b"], "cin_and_axorb")
    circuit3.add_a_gate_with_wires("or1", GateType.OR, ["a_and_b", "cin_and_axorb"], "cout")
    
    # Outputs
    circuit3.add_a_gate_with_wires("output_sum", GateType.OUTPUT, ["sum"], None)
    circuit3.add_a_gate_with_wires("output_cout", GateType.OUTPUT, ["cout"], None)
    
    circuit3.connect_gates()
    
    print(f"Gates: {len(circuit3.gates)}, Wires: {len(circuit3.wires)}")
    print("Logic: Full Adder with XOR, AND, OR gates")
    
    try:
        circuit3.generate_graph(layout='hierarchical', figsize=(14, 10), save_path='improved_circuit3.png')
        circuit3.export_to_dot('improved_circuit3.dot')
        print("✅ Improved graph generated!")
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")
    
    # Test 4: Complex circuit with NAND, NOR, XNOR
    print("\n=== Test 4: Complex Circuit with All Gate Types ===")
    circuit4 = Circuit()
    
    # Inputs
    circuit4.add_a_gate_with_wires("input_p", GateType.INPUT, [], "p")
    circuit4.add_a_gate_with_wires("input_q", GateType.INPUT, [], "q")
    circuit4.add_a_gate_with_wires("input_r", GateType.INPUT, [], "r")
    
    # Complex logic using various gate types
    circuit4.add_a_gate_with_wires("nand1", GateType.NAND, ["p", "q"], "nand_pq")
    circuit4.add_a_gate_with_wires("nor1", GateType.NOR, ["q", "r"], "nor_qr")
    circuit4.add_a_gate_with_wires("xor1", GateType.XOR, ["nand_pq", "nor_qr"], "xor_result")
    circuit4.add_a_gate_with_wires("xnor1", GateType.XNOR, ["xor_result", "r"], "xnor_result")
    circuit4.add_a_gate_with_wires("not1", GateType.NOT, ["xnor_result"], "not_result")
    circuit4.add_a_gate_with_wires("buf1", GateType.BUF, ["not_result"], "final")
    
    # Output
    circuit4.add_a_gate_with_wires("output", GateType.OUTPUT, ["final"], None)
    
    circuit4.connect_gates()
    
    print(f"Gates: {len(circuit4.gates)}, Wires: {len(circuit4.wires)}")
    print("Logic: Complex circuit with NAND, NOR, XOR, XNOR, NOT, BUF")
    
    try:
        circuit4.generate_graph(layout='hierarchical', figsize=(16, 12), save_path='improved_circuit4.png')
        circuit4.export_to_dot('improved_circuit4.dot')
        print("✅ Improved graph generated!")
    except ImportError:
        print("❌ Missing dependencies. Install with: pip install matplotlib networkx")
    
    print("\n" + "=" * 60)
    print("🎉 All improved circuit graphs generated!")
    print("\nKey Improvements:")
    print("✅ No wire nodes - cleaner visualization")
    print("✅ Proper gate shapes:")
    print("   📦 Rectangles: AND, NAND, Input, Output")
    print("   ⭕ Ellipses: OR, NOR")
    print("   💎 Diamonds: XOR, XNOR")
    print("   🔺 Triangles: NOT, BUF")
    print("✅ Hierarchical layout by default")
    print("✅ Cleaner labels and connections")
    
    print("\nGenerated files:")
    print("📁 PNG images: improved_circuit1.png, improved_circuit2.png, improved_circuit3.png, improved_circuit4.png")
    print("📁 DOT files: improved_circuit1.dot, improved_circuit2.dot, improved_circuit3.dot, improved_circuit4.dot")

if __name__ == "__main__":
    test_improved_graphs()
