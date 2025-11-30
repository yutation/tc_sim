"""
Deductive Fault Simulation (DFS) for efficient fault coverage analysis.

This module implements the Deductive Fault Simulation algorithm, which can
determine all faults detected by a test pattern in a single simulation pass.

The key idea: for each gate, maintain a set of faults that would cause its
output to differ from the fault-free value. These sets are propagated through
the circuit using deductive logic rules.

Reference:
E.G. Ulrich and T. Baker, "Concurrent simulation of nearly identical digital networks,"
Computer, vol. 7, no. 4, pp. 39-44, April 1974.
"""

import copy
from collections import deque
import os
from typing import Optional, Set, Dict, List
from . import circuit as cc
from .circuit import Circuit
from .gate import Gate, Wire, NodeValue, GateType
from . import fault as ft
from .fault import SSAFault
from . import utils


class DeductiveInfo:
    """
    Information tracked for each gate during deductive fault simulation.
    
    Attributes:
        fault_set: Set of faults that would cause this gate's output to differ
        valid: Whether this gate has been evaluated (for tracking purposes)
    """
    
    def __init__(self, fault_set: set[SSAFault] = None, valid: bool = False):
        """
        Initialize deductive information.
        
        Args:
            fault_set: Initial set of faults (defaults to empty set)
            valid: Whether this information is valid/computed
        """
        self.fault_set = fault_set if fault_set is not None else set()
        self.valid = valid
    
    def __str__(self):
        return f"DeductiveInfo({self.fault_set}, {self.valid})"
    
    def __repr__(self):
        return f"DeductiveInfo({self.fault_set}, {self.valid})"


class DeductiveFaultSimulator:
    """
    Deductive Fault Simulator for single-pass fault detection.
    
    This simulator evaluates a circuit with a specific input pattern and determines
    all stuck-at faults that would be detected by that pattern. It does this
    efficiently in a single pass by propagating fault sets through the circuit.
    
    Algorithm overview:
    1. Initialize each primary input with faults that affect it
    2. For each gate, compute the fault set based on input fault sets and gate function
    3. Collect all faults that reach primary outputs
    
    Attributes:
        circuit: The circuit to simulate (must already be evaluated)
        all_fault_set: Complete set of all possible faults in the circuit
    """
    def __init__(self, circuit: Circuit):
        """
        Initialize the deductive fault simulator.
        
        Args:
            circuit: The circuit to simulate (must be already evaluated with fault-free inputs)
            
        Raises:
            AssertionError: If circuit has not been evaluated
        """
        self.circuit = circuit
        assert self.circuit.evaluated, "Circuit must be evaluated before running deductive fault simulator"
        
        # Generate all possible stuck-at faults in the circuit
        self.all_fault_set = self.get_all_faults()
        
        # Pre-compute controlling values for faster lookup during simulation
        # Controlling value: if any input has this value, output is determined
        self._control_values = {
            GateType.AND: NodeValue.ZERO,   # 0 at any input → output is 0
            GateType.NAND: NodeValue.ZERO,  # 0 at any input → output is 1
            GateType.OR: NodeValue.ONE,     # 1 at any input → output is 1
            GateType.NOR: NodeValue.ONE     # 1 at any input → output is 0
        }

    def get_all_faults(self) -> Set[SSAFault]:
        """
        Generate all possible stuck-at faults for the circuit.
        
        For each wire, create two faults: stuck-at-0 and stuck-at-1.
        
        Returns:
            Set of all SSAFault objects for the circuit
        """
        all_fault_set = set()
        
        for wire in self.circuit.wires.values():
            # Create stuck-at-1 fault for this wire
            all_fault_set.add(SSAFault(wire.name, NodeValue.ONE))
            
            # Create stuck-at-0 fault for this wire
            all_fault_set.add(SSAFault(wire.name, NodeValue.ZERO))
        
        return all_fault_set


    def gate_deductive_eval(self, eval_gate: Gate, input_value_list: List[NodeValue], 
                           input_set_list: List[Set[SSAFault]]) -> Set[SSAFault]:
        """
        Perform deductive evaluation for a single gate.
        
        This function computes the fault set for a gate's output based on:
        1. The gate type and function
        2. Input values (fault-free values)
        3. Fault sets on each input
        
        The algorithm follows deductive logic rules specific to each gate type.
        
        Args:
            eval_gate: The gate to evaluate
            input_value_list: Fault-free values on each input
            input_set_list: Fault sets for each input
            
        Returns:
            The fault set for this gate's output
        """
        output_wire = eval_gate.fan_out_wire
        gate_type = eval_gate.type
        gate_output_value = eval_gate.output_value
        result_fault_set: Set[SSAFault] = set()
        
        # Output gates have no output wire, so no output fault to create
        if gate_type != GateType.OUTPUT:
            # The output fault: opposite of the fault-free output value
            output_fault = SSAFault(output_wire.name, ~gate_output_value)

        # Case 1: OUTPUT gate - just pass through the input fault set
        if gate_type == GateType.OUTPUT:
            assert len(input_set_list) == 1, "Output gate should have one input set list"
            result_fault_set = input_set_list[0]
        
        # Case 2: INPUT gate - only the output fault affects it
        elif gate_type == GateType.INPUT:
            assert len(input_set_list) == 0, "Input gate should have no input set list"
            if gate_output_value != NodeValue.UNKNOWN:
                # The output fault (opposite of the set value)
                result_fault_set.add(output_fault)
        
        # Case 3: NOT/BUF gates - simple propagation with output fault
        elif gate_type in [GateType.NOT, GateType.BUF]:
            assert len(input_set_list) == 1, "NOT or BUF gate should have one input set list"
            if gate_output_value != NodeValue.UNKNOWN:
                # Faults: input faults propagate through, plus output fault
                result_fault_set = input_set_list[0] | {output_fault}
            else:
                # Unknown output: just propagate input faults
                result_fault_set = input_set_list[0]
        # Case 4: AND/OR/NAND/NOR gates - use controlling/non-controlling value logic
        elif gate_type in [GateType.AND, GateType.OR, GateType.NAND, GateType.NOR]:
            # Get the controlling value for this gate type
            control_value = self._control_values.get(gate_type, NodeValue.UNKNOWN)
            
            # uc_set: union of fault sets on non-controlling inputs
            uc_set: Set[SSAFault] = set()
            
            # c_set: intersection of fault sets on controlling inputs
            c_set = self.all_fault_set.copy()  # Start with all faults
            
            have_control = False  # Any input at controlling value?
            x_count = 0  # Count of unknown inputs

            # Process each input
            for input_value, input_set in zip(input_value_list, input_set_list):
                if input_value == control_value:
                    # Controlling input: intersect fault sets
                    have_control = True
                    c_set &= input_set
                elif input_value == ~control_value:
                    # Non-controlling input: union fault sets
                    uc_set |= input_set
                elif input_value == NodeValue.UNKNOWN:
                    # Unknown input
                    x_count += 1
                else:
                    raise ValueError(f"Invalid input value {input_value}")
            
            # Compute result based on controlling values
            if x_count == 0:
                if have_control:
                    # Have controlling input: faults on controlling inputs minus
                    # faults on non-controlling inputs, plus output fault
                    result_fault_set = (c_set - uc_set) | {output_fault}
                else:
                    # All non-controlling: union of all input faults plus output fault
                    result_fault_set = uc_set | {output_fault}
            elif have_control:
                # Have controlling input but also unknowns: only output fault matters
                result_fault_set = {output_fault}
        # Case 5: XOR/XNOR gates - use symmetric difference (XOR) on fault sets
        elif gate_type in [GateType.XOR, GateType.XNOR]:
            c_set: Set[SSAFault] = set()
            x_count = 0
            
            # XOR the fault sets: a fault appears in output if it appears in
            # odd number of inputs
            for input_value, input_set in zip(input_value_list, input_set_list):
                if input_value == NodeValue.UNKNOWN:
                    x_count += 1
                c_set ^= input_set  # Symmetric difference (XOR)
            
            if x_count == 0:
                # No unknowns: result is XOR of input sets plus output fault
                result_fault_set = c_set | {output_fault}
        
        else:
            raise ValueError(f"Invalid gate type {gate_type}")
            
        return result_fault_set

    def deductive_eval(self) -> Set[SSAFault]:
        """
        Perform deductive fault simulation on the circuit.
        
        This is the main simulation algorithm that:
        1. Starts from primary inputs
        2. Propagates fault sets through the circuit in topological order
        3. Collects all faults that reach primary outputs
        
        The circuit must already be evaluated with fault-free inputs before calling.
        
        Returns:
            Set of all faults detected at primary outputs
        """
        # BFS queue for topological traversal
        evaluation_queue = deque()
        
        # Final result: faults detected at outputs
        final_fault_set: Set[SSAFault] = set()
        
        # Track deductive info for each gate
        deductive_info_dict: Dict[str, DeductiveInfo] = {}
        
        def add_fan_out_gates_to_queue(gate: Gate):
            """Helper to add all fan-out gates to the evaluation queue."""
            evaluation_queue.extend(gate.fan_out_gates)
        
        # Initialize queue with primary input gates
        for input_port_name in self.circuit.input_port_names:
            input_port_gate = self.circuit.gates[input_port_name]
            evaluation_queue.append(input_port_gate)

        # Process gates in topological order (BFS)
        while evaluation_queue:
            # Debugging: uncomment to see evaluation order
            # print("queue: ", [gate.name for gate in evaluation_queue])
            current_gate: Gate = evaluation_queue.popleft()
            
            # Skip if already evaluated (can happen due to multiple fan-outs)
            if current_gate.name in deductive_info_dict:
                continue
            
            # Debugging: uncomment to trace evaluation
            # print("current_gate: ", current_gate.name)
            # print("deductive_info_dict: ", deductive_info_dict.keys())
            
            # Handle INPUT gates
            if current_gate.type == GateType.INPUT:
                # Input gates have no inputs, compute their fault set
                result_fault_set = self.gate_deductive_eval(current_gate, [], [])
                deductive_info_dict[current_gate.name] = DeductiveInfo(result_fault_set, True)
                add_fan_out_gates_to_queue(current_gate)
            
            # Handle OUTPUT gates
            elif current_gate.type == GateType.OUTPUT:
                # Output gate: get fault set from its single input
                fan_in_gate = current_gate.fan_in_gates[0]
                input_set = deductive_info_dict[fan_in_gate.name].fault_set
                input_value = fan_in_gate.output_value
                
                result_fault_set = self.gate_deductive_eval(current_gate, [input_value], [input_set])
                deductive_info_dict[current_gate.name] = DeductiveInfo(result_fault_set, True)
                
                # Collect faults detected at this output
                final_fault_set |= result_fault_set
            
            # Handle internal logic gates
            else:
                input_set_list: List[Set[SSAFault]] = []
                ready_to_eval = True
                
                # Check if all inputs have been evaluated
                for fan_in_gate in current_gate.fan_in_gates:
                    if fan_in_gate.name not in deductive_info_dict:
                        # Not ready yet, skip for now
                        ready_to_eval = False
                        break
                    input_set_list.append(deductive_info_dict[fan_in_gate.name].fault_set)
                
                # Skip if inputs not ready (will be re-queued by fan-in gates)
                if not ready_to_eval:
                    continue
                
                # Collect input values and evaluate the gate
                input_value_list = [gate.output_value for gate in current_gate.fan_in_gates]
                result_fault_set = self.gate_deductive_eval(current_gate, input_value_list, input_set_list)
                deductive_info_dict[current_gate.name] = DeductiveInfo(result_fault_set, True)
                
                # Add fan-out gates to queue for further propagation
                add_fan_out_gates_to_queue(current_gate)
        
        return final_fault_set


class DFSWrapper:
    """
    Wrapper class for running Deductive Fault Simulation on multiple test patterns.
    
    This class provides a convenient interface for:
    - Loading a circuit from a netlist file
    - Loading test patterns from a file
    - Running DFS on all test patterns
    - Saving detected fault lists to files
    
    Attributes:
        circuit: The circuit loaded from the netlist
        circuit_file: Path to the circuit file
        fault_set_file: Path to the fault set file (optional)
        test_pattern_str_list: List of test patterns as strings
        all_fault_set: Set of faults to consider (None = all faults)
        found_fault_set_list: List of detected fault sets (one per test pattern)
    """
    
    def __init__(self, circuit_file: str, fault_set_file: Optional[str] = None):
        """
        Initialize the DFS wrapper with a circuit file.
        
        Args:
            circuit_file: Path to the circuit netlist file
            fault_set_file: Optional path to fault list file (limits which faults to check)
        """
        self.circuit = cc.build_circuit_from_ECE6140_netlist(circuit_file)
        self.circuit_file = circuit_file
        self.fault_set_file = fault_set_file
        self.test_pattern_str_list = []
        
        # Load fault set if provided (otherwise, all faults will be considered)
        self.all_fault_set = self.parse_fault_set_file(fault_set_file) if fault_set_file is not None else None
        self.found_fault_set_list = []

    def add_test_pattern_from_file(self, test_pattern_file: str):
        """
        Load test patterns from a file.
        
        Args:
            test_pattern_file: Path to file containing test patterns (one per line)
        """
        self.test_pattern_str_list.extend(self.parse_test_pattern_file(test_pattern_file))
    
    def parse_fault_set_file(self, fault_set_file: str) -> Set[SSAFault]:
        """
        Parse a fault list file into a set of SSAFault objects.
        
        Args:
            fault_set_file: Path to the fault list file
            
        Returns:
            Set of SSAFault objects
        """
        fault_pairs = ft.read_fault_file(fault_set_file)
        fault_set = set()
        for node_name, fault_value in fault_pairs:
            fault_set.add(SSAFault(node_name, fault_value))
        return fault_set

    def parse_test_pattern_file(self, test_pattern_file: str) -> List[str]:
        """
        Parse a test pattern file into a list of pattern strings.
        
        Args:
            test_pattern_file: Path to file with test patterns (one per line)
            
        Returns:
            List of test pattern strings
        """
        test_pattern_list = []
        with open(test_pattern_file, 'r') as file:
            for line in file:
                line = line.strip()
                test_pattern_list.append(line)
        return test_pattern_list

    def run(self, input_values: str) -> List[SSAFault]:
        """
        Run deductive fault simulation for a single test pattern.
        
        Args:
            input_values: Test pattern as a string (e.g., "10110")
            
        Returns:
            Sorted list of faults detected by this test pattern
        """
        self.str_input_values = input_values
        input_node_values = cc.str_inputs_to_node_values(input_values)
        
        # Evaluate circuit with the test pattern
        self.circuit.reset_gates()
        self.circuit.set_inputs(input_node_values)
        self.circuit.evaluate()
        
        # Run deductive fault simulation
        deductive_fault_simulator = DeductiveFaultSimulator(self.circuit)
        final_fault_set = deductive_fault_simulator.deductive_eval()
        
        # Filter to only faults in the specified fault set (if provided)
        if self.all_fault_set is not None:
            final_fault_set &= self.all_fault_set
        
        # Sort by node name for consistent output
        sorted_final_fault_set = ft.sort_ssa_faults_by_node_name(list(final_fault_set))
        return sorted_final_fault_set

    def run_all_test_patterns(self) -> List[List[SSAFault]]:
        """
        Run deductive fault simulation for all loaded test patterns.
        
        Returns:
            List of fault sets, one for each test pattern
        """
        self.found_fault_set_list = []
        for test_pattern_str in self.test_pattern_str_list:
            found_fault_set = self.run(test_pattern_str)
            self.found_fault_set_list.append(found_fault_set)
        return self.found_fault_set_list

    def save_detected_fault_set_verbose(self, detected_fault_set: List[SSAFault], 
                                       input_values: str, output_file: str):
        """
        Save detected faults to a file with verbose information.
        
        Includes header with circuit info, input pattern, and fault count.
        
        Args:
            detected_fault_set: List of detected faults
            input_values: The test pattern used
            output_file: Path to output file
        """
        with open(output_file, 'w') as file:
            # Write header information
            file.write(f"Circuit file: {self.circuit_file}\n")
            file.write(f"Fault set file: {self.fault_set_file}\n")
            file.write(f"Input values: {input_values}\n")
            file.write(f"Detected faults: {len(detected_fault_set)}\n")
            file.write(f"------FAULTS DETECTED------\n")
            
            # Write each detected fault
            for fault in detected_fault_set:
                node_name = fault.node_name
                if fault.fault_value == NodeValue.ZERO:
                    digit_fault_value = 0
                elif fault.fault_value == NodeValue.ONE:
                    digit_fault_value = 1
                else:
                    digit_fault_value = 2
                fault_str = f"{node_name} stuck at {digit_fault_value}"
                file.write(fault_str + '\n')
        
        print(f"Detected faults for input values {input_values} have been saved to {output_file}")

    def save_detected_fault_set_v2(self, detected_fault_set: List[SSAFault], 
                                   input_values: str, output_file1: str, output_file2: str):
        """
        Save detected faults to two files: header in file1, faults in file2.
        
        Args:
            detected_fault_set: List of detected faults
            input_values: The test pattern used
            output_file1: Path to header file
            output_file2: Path to fault list file
        """
        # Write header information to first file
        with open(output_file1, 'w') as file:
            file.write(f"Circuit file: {self.circuit_file}\n")
            file.write(f"Fault set file: {self.fault_set_file}\n")
            file.write(f"Input values: {input_values}\n")
            file.write(f"Detected faults: {len(detected_fault_set)}\n")
            file.write(f"------FAULTS DETECTED------\n")
        
        # Write fault list to second file
        with open(output_file2, 'w') as file:
            for fault in detected_fault_set:
                node_name = fault.node_name
                if fault.fault_value == NodeValue.ZERO:
                    digit_fault_value = 0
                elif fault.fault_value == NodeValue.ONE:
                    digit_fault_value = 1
                else:
                    digit_fault_value = 2
                fault_str = f"{node_name} stuck at {digit_fault_value}"
                file.write(fault_str + '\n')
        
        print(f"Detected faults have been saved to {output_file1} and {output_file2}")

    def save_detected_fault_set(self, detected_fault_set: List[SSAFault], 
                                input_values: str, output_file: str):
        """
        Save detected faults to a file (fault list only, no header).
        
        Args:
            detected_fault_set: List of detected faults
            input_values: The test pattern used
            output_file: Path to output file
        """
        with open(output_file, 'w') as file:
            for fault in detected_fault_set:
                node_name = fault.node_name
                if fault.fault_value == NodeValue.ZERO:
                    digit_fault_value = 0
                elif fault.fault_value == NodeValue.ONE:
                    digit_fault_value = 1
                else:
                    digit_fault_value = 2
                fault_str = f"{node_name} stuck at {digit_fault_value}"
                file.write(fault_str + '\n')
        
        print(f"Detected faults for input values {input_values} have been saved to {output_file}")


    def save_detected_fault_set_list_verbose(self, file_path: str):
        """
        Save all detected fault sets with verbose information (one file per test pattern).
        
        Creates multiple output files named: base_name_0.ext, base_name_1.ext, etc.
        
        Args:
            file_path: Base path for output files
        """
        directory, file_name_without_extension, extension = utils.prepare_output_file(file_path)
        
        for i, detected_fault_set in enumerate(self.found_fault_set_list):
            output_file = os.path.join(directory, f"{file_name_without_extension}_{i}{extension}")
            self.save_detected_fault_set_verbose(detected_fault_set, 
                                                 self.test_pattern_str_list[i], 
                                                 output_file)

    def save_detected_fault_set_list(self, file_path: str):
        """
        Save all detected fault sets (one file per test pattern, no headers).
        
        Creates multiple output files named: base_name_0.ext, base_name_1.ext, etc.
        
        Args:
            file_path: Base path for output files
        """
        directory, file_name_without_extension, extension = utils.prepare_output_file(file_path)
        
        for i, detected_fault_set in enumerate(self.found_fault_set_list):
            output_file = os.path.join(directory, f"{file_name_without_extension}_{i}{extension}")
            self.save_detected_fault_set(detected_fault_set, 
                                        self.test_pattern_str_list[i], 
                                        output_file)     
