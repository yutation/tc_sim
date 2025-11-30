"""
Circuit module for digital circuit simulation.

This module provides classes for building and simulating digital circuits:
- Wire: Connects gates together
- Circuit: Manages gates, wires, and circuit evaluation
- CircuitWrapper: Parses circuit files and builds circuits from netlists

The circuit evaluation uses a BFS-based approach to propagate values
through the gate network.
"""

from collections import deque
from typing import Dict, Optional
import matplotlib.pyplot as plt
import networkx as nx
from .gate import Gate, GateType, NodeValue, Wire
from .fault import SSAFault




class Circuit:
    """
    Represents a complete digital circuit with gates and wires.
    
    The Circuit class manages all gates and wires in a circuit, handles
    circuit construction, evaluation, and visualization. It supports both
    manual circuit building and evaluation with various input patterns.
    
    Attributes:
        wires: Dictionary mapping wire names to Wire objects
        gates: Dictionary mapping gate names to Gate objects
        input_port_names: List of primary input gate names
        output_port_names: List of primary output gate names
    """
    def __init__(self):
        self.wires: Dict[str, Wire] = {}
        self.gates: Dict[str, Gate] = {}
        self.input_port_names: list[str] = []
        self.output_port_names: list[str] = []
        self.evaluated = False
        
    def add_a_gate_with_wires(self, gate_name: str, gate_type: GateType, input_wire_names: list[str], output_wire_name: Optional[str]):
        """
        Add a gate to the circuit along with its wire connections.
        
        Creates or reuses wires as needed to connect the gate. For INPUT gates,
        the gate is added to the input port list. For OUTPUT gates, it's added
        to the output port list.
        
        Args:
            gate_name: Unique identifier for the gate
            gate_type: Type of gate to create
            input_wire_names: List of wire names providing input to this gate
            output_wire_name: Name of wire receiving output from this gate (None for OUTPUT gates)
            
        Raises:
            AssertionError: If a gate with this name already exists
        """
        assert gate_name not in self.gates, "Gate already exists"
        
        # Create the gate with the appropriate number of inputs
        input_number = len(input_wire_names)
        local_gate = gate_type.create_gate(gate_name, input_number)
        self.gates[gate_name] = local_gate

        # Track primary input and output gates
        if gate_type == GateType.INPUT:
            self.input_port_names.append(gate_name)
        elif gate_type == GateType.OUTPUT:
            self.output_port_names.append(gate_name)

        # Connect input wires to this gate
        for input_wire_name in input_wire_names:
            # Create wire if it doesn't exist
            if input_wire_name not in self.wires:
                local_wire = Wire(input_wire_name)
                self.wires[input_wire_name] = local_wire
            else:
                local_wire = self.wires[input_wire_name]
            
            # This gate reads from the wire
            local_wire.add_output_gate(local_gate)
            local_gate.add_fan_in_wire(local_wire)
        
        # Connect output wire from this gate
        if output_wire_name is not None:
            # Create wire if it doesn't exist
            if output_wire_name not in self.wires:
                local_wire = Wire(output_wire_name)
                self.wires[output_wire_name] = local_wire
            else:
                local_wire = self.wires[output_wire_name]
            # This gate drives the wire
            local_wire.add_input_gate(local_gate)
            local_gate.add_fan_out_wire(local_wire)

    def connect_gates(self):
        """
        Establish all gate-to-gate connections through wires.
        
        Must be called after all gates and wires have been added to finalize
        the circuit topology before evaluation.
        """
        for wire in self.wires.values():
            wire.connect_gates()

    def evaluate(self):
        """
        Evaluate the circuit using breadth-first propagation.
        
        Starting from primary inputs, propagates values through the circuit
        using a BFS approach. Gates are re-evaluated when their inputs change.
        The evaluation continues until all reachable gates have stable outputs.
        
        Raises:
            AssertionError: If a cycle is detected (gate value changes unexpectedly)
        """
        # Initialize BFS queue with gates immediately following primary inputs
        evaluation_queue = deque()
        for input_port_name in self.input_port_names:
            evaluation_queue.extend(self.gates[input_port_name].fan_out_gates)

        # Propagate values through the circuit
        while len(evaluation_queue) > 0:
            gate: Gate = evaluation_queue.popleft()
            prev_output_value = gate.output_value
            new_output_value = gate.forward()
            
            # If output didn't change, no need to propagate further
            if prev_output_value == new_output_value:
                continue
            
            # Sanity check: output should only change from UNKNOWN (no cycles)
            assert prev_output_value == NodeValue.UNKNOWN, "It may have cycle in the circuit"
            
            # Add downstream gates to the evaluation queue
            for fan_out_gate in gate.fan_out_gates:
                evaluation_queue.append(fan_out_gate)
        
        self.evaluated = True

    def evaluate_with_fault(self, fault: SSAFault):
        """
        Evaluate the circuit with a fault.
        
        Args:
            fault: The fault to evaluate the circuit with
        """
        fault_backward_gate = fault.get_backward_gate()
        evaluation_queue = deque()
        for input_port_name in self.input_port_names:
            evaluation_queue.extend(self.gates[input_port_name].fan_out_gates)
            if input_port_name == fault_backward_gate.name:
                self.gates[input_port_name].set_output_value(fault.get_fault_d_value())

        # Propagate values through the circuit
        while len(evaluation_queue) > 0:
            gate: Gate = evaluation_queue.popleft()
            prev_output_value = gate.output_value
            new_output_value = gate.forward()

            # Fault insertion
            if gate.name == fault_backward_gate.name:
                if new_output_value == fault.get_activation_value():
                    gate.set_output_value(fault.get_fault_d_value())

            # If output didn't change, no need to propagate further
            if prev_output_value == new_output_value:
                continue
            
            # Add downstream gates to the evaluation queue
            for fan_out_gate in gate.fan_out_gates:
                evaluation_queue.append(fan_out_gate)
        
        self.evaluated = True
        
    
    def set_inputs(self, input_values: list[NodeValue]):
        assert len(input_values) == len(self.input_port_names), "Input values must match the number of input ports"
        for i, input_name in enumerate(self.input_port_names):
            input_gate = self.gates[input_name]
            input_gate.set_output_value(input_values[i])

    def set_input_value(self, input_name: str, input_value: NodeValue):
        input_gate = self.gates[input_name]
        input_gate.set_output_value(input_value)

    def get_outputs(self):
        output_values = []
        for output_name in self.output_port_names:
            output_gate = self.gates[output_name]
            output_values.append(output_gate.output_value)
        return output_values

    def get_output_gates(self) -> list[Gate]:
        output_gates = []
        for output_name in self.output_port_names:
            output_gates.append(self.gates[output_name])
        return output_gates

    def reset_gates(self):
        """
        Reset all gates in the circuit to their initial state.
        
        Clears all gate values and evaluation counts, preparing the circuit
        for a fresh evaluation.
        """
        for gate in self.gates.values():
            gate.reset_values()
        self.evaluated = False

    def get_a_ssa_fault(self, wire_name: str, fault_value: NodeValue) -> SSAFault:

        wire = self.wires[wire_name]
        return SSAFault(wire_name, fault_value, parameters={"wire": wire, "forward_gates": wire.output_gates, "backward_gate": wire.input_gate})

    def get_state_string(self) -> str:
        state_string = "{"
        for gate in self.gates.values():
            state_string += "(" + gate.name + " " + str(gate.output_value) + "), "
        state_string += "}"
        return state_string

    def export_to_dot(self, filename=None):
        """
        Export circuit to DOT format for use with Graphviz.
        
        Generates a DOT language representation of the circuit suitable for
        rendering with Graphviz tools. Different gate types are assigned
        appropriate shapes and colors.
        
        Args:
            filename: Optional filename to save the DOT file (if None, returns string)
            
        Returns:
            String containing the complete DOT representation
        """
        dot_lines = ["digraph Circuit {"]
        dot_lines.append("    rankdir=LR;")  # Left-to-right layout
        dot_lines.append("    node [style=filled];")
        
        # Add all gates as nodes with shapes based on type
        for gate_name, gate in self.gates.items():
            if gate_name in self.input_port_names:
                # Input gates - rectangles
                wire_name = gate_name.replace('input_', '')
                dot_lines.append(f"    \"{gate_name}\" [shape=box, fillcolor=lightgreen, label=\"{wire_name}\\n(IN)\"];")
            elif gate_name in self.output_port_names:
                # Output gates - rectangles
                wire_name = gate_name.replace('output_', '')
                dot_lines.append(f"    \"{gate_name}\" [shape=box, fillcolor=lightcoral, label=\"{wire_name}\\n(OUT)\"];")
            else:
                # Logic gates with appropriate shapes
                gate_type = gate.type.value
                gate_label = gate_name.split('_')[-1] if '_' in gate_name else gate_name
                
                if gate_type in ['AND', 'NAND']:
                    # AND/NAND gates - rectangular
                    dot_lines.append(f"    \"{gate_name}\" [shape=box, fillcolor=lightblue, label=\"{gate_type}\\n{gate_label}\"];")
                elif gate_type in ['OR', 'NOR']:
                    # OR/NOR gates - rounded rectangle
                    dot_lines.append(f"    \"{gate_name}\" [shape=ellipse, fillcolor=lightblue, label=\"{gate_type}\\n{gate_label}\"];")
                elif gate_type in ['XOR', 'XNOR']:
                    # XOR/XNOR gates - diamond shape
                    dot_lines.append(f"    \"{gate_name}\" [shape=diamond, fillcolor=lightblue, label=\"{gate_type}\\n{gate_label}\"];")
                elif gate_type in ['NOT', 'BUF']:
                    # NOT/BUF gates - triangle
                    dot_lines.append(f"    \"{gate_name}\" [shape=triangle, fillcolor=lightblue, label=\"{gate_type}\\n{gate_label}\"];")
                else:
                    # Default shape
                    dot_lines.append(f"    \"{gate_name}\" [shape=box, fillcolor=lightblue, label=\"{gate_type}\\n{gate_label}\"];")
        
        # Add edges representing direct gate-to-gate connections
        dot_lines.append("    // Connections")
        for gate_name, gate in self.gates.items():
            for fan_out_gate in gate.fan_out_gates:
                dot_lines.append(f"    \"{gate_name}\" -> \"{fan_out_gate.name}\";")
        
        dot_lines.append("}")
        
        dot_content = "\n".join(dot_lines)
        
        # Save to file if filename provided
        if filename:
            with open(filename, 'w') as f:
                f.write(dot_content)
            print(f"Circuit exported to {filename}")
        
        return dot_content


def build_circuit_from_ECE6140_netlist(netlist_file: str) -> Circuit:
    """
    Parse the circuit file and build the circuit structure.
    
    Reads the netlist file line by line, creating gates and wires
    according to the specifications. Ignores comments (lines starting
    with // or #) and empty lines.
    
    After parsing, connects all gates through their wires to establish
    the complete circuit topology.
    """
    circuit = Circuit()
    with open(netlist_file, 'r') as file:
        for line in file:
            line = line.strip()
            # Skip comments and empty lines
            if line.startswith('//') or line.startswith('#') or not line:
                continue
            
            parts = line.split()
            if not parts:
                continue
            
            gate_type_str = parts[0]
            
            # Parse INPUT port declarations
            if gate_type_str == 'INPUT':
                # Format: INPUT wire1 wire2 ... -1
                wire_names = []
                for part in parts[1:]:
                    if part == '-1':  # Terminator
                        break
                    wire_names.append(part)
                
                # Create an INPUT gate for each primary input wire
                for wire_name in wire_names:
                    gate_name = f"input_{wire_name}"
                    circuit.add_a_gate_with_wires(
                        gate_name, 
                        GateType.INPUT, 
                        [],          # INPUT gates have no input wires
                        wire_name    # They output to a wire
                    )
            
            # Parse OUTPUT port declarations
            elif gate_type_str == 'OUTPUT':
                # Format: OUTPUT wire1 wire2 ... -1
                wire_names = []
                for part in parts[1:]:
                    if part == '-1':  # Terminator
                        break
                    wire_names.append(part)
                
                # Create an OUTPUT gate for each primary output wire
                for wire_name in wire_names:
                    gate_name = f"output_{wire_name}"
                    circuit.add_a_gate_with_wires(
                        gate_name, 
                        GateType.OUTPUT, 
                        [wire_name],  # Read from a wire
                        None          # OUTPUT gates have no output wire
                    )
            
            # Parse logic gate definitions
            else:
                # Format: GATE_TYPE input1 input2 ... output
                if len(parts) < 3:  # Need at least: gate_type, one input, one output
                    print(f"Invalid line: {line}")
                    continue
                
                gate_type_str = parts[0]
                input_wires = parts[1:-1]  # All middle parts are inputs
                output_wire = parts[-1]    # Last part is the output
                
                # Map netlist gate names to GateType enum
                gate_type_map = {
                    'INV': GateType.NOT,
                    'BUF': GateType.BUF,
                    'AND': GateType.AND,
                    'OR': GateType.OR,
                    'NAND': GateType.NAND,
                    'NOR': GateType.NOR,
                    'XOR': GateType.XOR,
                    'XNOR': GateType.XNOR
                }
                
                if gate_type_str in gate_type_map:
                    gate_type = gate_type_map[gate_type_str]
                    # Create unique gate name using type and output wire
                    gate_name = f"{gate_type_str.lower()}_{output_wire}"
                    
                    circuit.add_a_gate_with_wires(
                        gate_name,
                        gate_type,
                        input_wires,
                        output_wire
                    )
                else:
                    print(f"Invalid gate type: {gate_type_str}")
    
    # Finalize all gate connections
    circuit.connect_gates()
    return circuit

def str_inputs_to_node_values(input_values: str):
    node_values = []
    for input_value in input_values:
        if input_value == '0':
            node_values.append(NodeValue.ZERO)
        elif input_value == '1':
            node_values.append(NodeValue.ONE)
        elif input_value == 'X':
            node_values.append(NodeValue.UNKNOWN)
        else:
            raise ValueError(f"Invalid input value: {input_value}")
    return node_values

def node_values_to_str(node_values: list[NodeValue]) -> str:
    str_values = []
    for node_value in node_values:
        if node_value == NodeValue.ZERO:
            str_values.append('0')
        elif node_value == NodeValue.ONE:
            str_values.append('1')
        elif node_value == NodeValue.UNKNOWN:
            str_values.append('X')
        elif node_value == NodeValue.D:
            str_values.append('D')
        elif node_value == NodeValue.D_BAR:
            str_values.append('D\'')
        else:
            raise ValueError(f"Invalid node value: {node_value}")
    return ''.join(str_values)


class CircuitWrapper:
    """
    Wrapper class for building circuits from netlist files.
    
    Parses circuit description files and constructs a Circuit object.
    The file format supports:
    - INPUT declarations: INPUT wire1 wire2 ... -1
    - OUTPUT declarations: OUTPUT wire1 wire2 ... -1
    - Gate definitions: GATE_TYPE input1 input2 ... output
    
    Supported gate types: AND, OR, NAND, NOR, XOR, XNOR, INV (NOT), BUF
    
    Attributes:
        circuit_file: Path to the circuit netlist file
        circuit: The constructed Circuit object
    """
    def __init__(self, circuit_file: str):
        """
        Initialize the CircuitWrapper with a circuit file.
        
        Args:
            circuit_file: Path to the netlist file describing the circuit
        """
        self.circuit_file = circuit_file
        self.circuit = Circuit()
    
    def build_circuit(self):
        self.circuit = build_circuit_from_ECE6140_netlist(self.circuit_file)

    def evaluate_circuit_with_normal_input(self, input_values: str):
        """
        Evaluate the circuit with a binary input pattern.
        
        Sets the primary inputs to the specified values (0 or 1), evaluates
        the circuit, and returns the resulting output values.
        
        Args:
            input_values: String of '0' and '1' characters, one per primary input
            
        Returns:
            String of '0', '1', or 'X' (unknown) characters representing outputs
            
        Raises:
            ValueError: If input length doesn't match number of primary inputs
                       or if input contains invalid characters
        """
        # Reset all gates to unknown state before new evaluation
        self.circuit.reset_gates()
        
        # Validate input length
        expected_inputs = len(self.circuit.input_port_names)
        if len(input_values) != expected_inputs:
            raise ValueError(f"Expected {expected_inputs} input values, got {len(input_values)}")
        
        input_values = str_inputs_to_node_values(input_values)
        # Apply input values to primary input gates
        self.circuit.set_inputs(input_values)
        
        # Propagate values through the circuit
        self.circuit.evaluate()
        
        output_values = self.circuit.get_outputs()
        
        # Collect and format output values
        str_output_values = []
        for output_value in output_values:
            if output_value == NodeValue.ZERO:
                str_output_values.append('0')
            elif output_value == NodeValue.ONE:
                str_output_values.append('1')
            else:
                str_output_values.append('X')  # Unknown/uninitialized value
        
        return ''.join(output_values)


