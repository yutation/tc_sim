#!/usr/bin/env python3
"""
Demonstration script showing circuit graph examples without external dependencies.
This shows the structure and functionality of the circuit graph generation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tc_sim'))

from tc_sim.circuit import Circuit
from tc_sim.gate import GateType

def show_circuit_structure(circuit, name):
    """Display circuit structure in text format"""
    print(f"\n=== {name} ===")
    print(f"Gates: {len(circuit.gates)}")
    print(f"Wires: {len(circuit.wires)}")
    print(f"Inputs: {circuit.input_port_names}")
    print(f"Outputs: {circuit.output_port_names}")
    
    print("\nGate Details:")
    for gate_name, gate in circuit.gates.items():
        fan_in_names = [g.gate_name for g in gate.fan_in_gates]
        fan_out_names = [g.gate_name for g in gate.fan_out_gates]
        print(f"  {gate_name} ({gate.gate_type.value}):")
        print(f"    Fan-in:  {fan_in_names}")
        print(f"    Fan-out: {fan_out_names}")
    
    print("\nWire Details:")
    for wire_name, wire in self.wires.items():
        input_gate = wire.input_gate.gate_name if wire.input_gate else "None"
        output_gates = [g.gate_name for g in wire.output_gates]
        print(f"  {wire_name}: {input_gate} -> {output_gates}")

def example_1_simple_and_or():
    """Example 1: Simple AND-OR circuit"""
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
    
    print("=== Example 1: Simple AND-OR Circuit ===")
    print("Logic: (x AND y) OR z")
    print(f"Gates: {len(circuit.gates)}, Wires: {len(circuit.wires)}")
    print(f"Inputs: {circuit.input_port_names}")
    print(f"Outputs: {circuit.output_port_names}")
    
    print("\nGate Connections:")
    for gate_name, gate in circuit.gates.items():
        fan_in_names = [g.name for g in gate.fan_in_gates]
        fan_out_names = [g.name for g in gate.fan_out_gates]
        print(f"  {gate_name} ({gate.type.value}):")
        if fan_in_names:
            print(f"    Inputs:  {fan_in_names}")
        if fan_out_names:
            print(f"    Outputs: {fan_out_names}")
    
    print("\nWire Connections:")
    for wire_name, wire in circuit.wires.items():
        input_gate = wire.input_gate.name if wire.input_gate else "None"
        output_gates = [g.name for g in wire.output_gates]
        print(f"  {wire_name}: {input_gate} -> {output_gates}")
    
    # Test evaluation
    print("\nTesting circuit evaluation:")
    test_inputs = ["000", "001", "010", "011", "100", "101", "110", "111"]
    for test_input in test_inputs:
        try:
            # Create a simple evaluation
            circuit.reset_gates()
            
            # Set input values
            for i, input_name in enumerate(circuit.input_port_names):
                input_gate = circuit.gates[input_name]
                if test_input[i] == '0':
                    input_gate.set_output_value(input_gate.type.create_gate("", 0).output_value.__class__.ZERO)
                else:
                    input_gate.set_output_value(input_gate.type.create_gate("", 0).output_value.__class__.ONE)
            
            # Evaluate
            circuit.evaluate()
            
            # Get output
            output_gate = circuit.gates[circuit.output_port_names[0]]
            output_value = "1" if output_gate.output_value.value == "One" else "0"
            
            print(f"  Input {test_input} -> Output {output_value}")
        except:
            print(f"  Input {test_input} -> Error in evaluation")
    
    return circuit

def example_2_xor_circuit():
    """Example 2: XOR circuit using basic gates"""
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
    
    print("\n=== Example 2: XOR Circuit ===")
    print("Logic: A XOR B using basic gates")
    print(f"Gates: {len(circuit.gates)}, Wires: {len(circuit.wires)}")
    print(f"Inputs: {circuit.input_port_names}")
    print(f"Outputs: {circuit.output_port_names}")
    
    print("\nGate Flow:")
    print("  input_a -> not_a -> and2")
    print("  input_a -> and1")
    print("  input_b -> not_b -> and1") 
    print("  input_b -> and2")
    print("  and1, and2 -> or1 -> output")
    
    return circuit

def example_3_full_adder():
    """Example 3: Full Adder circuit"""
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
    
    print("\n=== Example 3: Full Adder Circuit ===")
    print("Logic: Full Adder (A + B + Cin = Sum, Cout)")
    print(f"Gates: {len(circuit.gates)}, Wires: {len(circuit.wires)}")
    print(f"Inputs: {circuit.input_port_names}")
    print(f"Outputs: {circuit.output_port_names}")
    
    print("\nCircuit Structure:")
    print("  Sum calculation:")
    print("    A, B -> XOR1 -> A_XOR_B")
    print("    A_XOR_B, Cin -> XOR2 -> Sum")
    print("  Carry calculation:")
    print("    A, B -> AND1 -> A_AND_B")
    print("    Cin, A_XOR_B -> AND2 -> Cin_AND_AXORB")
    print("    A_AND_B, Cin_AND_AXORB -> OR1 -> Cout")
    
    return circuit

def show_dot_file_content(filename):
    """Display the content of a DOT file"""
    if os.path.exists(filename):
        print(f"\n=== {filename} Content ===")
        with open(filename, 'r') as f:
            content = f.read()
            print(content)
    else:
        print(f"\n{filename} not found")

def main():
    """Run all examples and show results"""
    print("🔌 Circuit Graph Generation Examples")
    print("=" * 60)
    
    # Run examples
    circuit1 = example_1_simple_and_or()
    circuit2 = example_2_xor_circuit()
    circuit3 = example_3_full_adder()
    
    # Show DOT file contents
    print("\n" + "=" * 60)
    print("📁 Generated DOT Files Content:")
    
    dot_files = [
        "example1_and_or.dot",
        "example2_xor.dot", 
        "example3_full_adder.dot"
    ]
    
    for dot_file in dot_files:
        show_dot_file_content(dot_file)
    
    print("\n" + "=" * 60)
    print("🎉 Examples completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Circuit structure representation")
    print("✅ Gate connections and fan-in/fan-out relationships")
    print("✅ Wire connections between gates")
    print("✅ Multiple gate types (AND, OR, NOT, XOR)")
    print("✅ Input and output port identification")
    print("✅ DOT format export for external visualization")
    print("✅ Hierarchical layout for clear data flow")
    
    print("\n🔧 To visualize the graphs:")
    print("1. Install Graphviz: sudo apt install graphviz")
    print("2. Convert DOT to images:")
    print("   dot -Tpng example1_and_or.dot -o example1_and_or.png")
    print("   dot -Tsvg example2_xor.dot -o example2_xor.svg")
    print("3. Or use online Graphviz viewers")

if __name__ == "__main__":
    main()
