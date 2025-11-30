"""
PODEM (Path-Oriented Decision Making) test pattern generation algorithm.

This module implements the PODEM algorithm for automatic test pattern generation (ATPG).
PODEM uses a recursive backtracking approach to find test patterns that detect
specific stuck-at faults in digital circuits.

The algorithm consists of three main phases:
1. Objective selection: Choose a gate/value to set for fault activation or propagation
2. Backtrace: Trace back from the objective to a primary input
3. Implication: Set the input and propagate values through the circuit

Reference:
P. Goel, "An Implicit Enumeration Algorithm to Generate Tests for Combinational Logic Circuits,"
IEEE Transactions on Computers, vol. C-30, no. 3, pp. 215-222, March 1981.
"""

import os
from typing import List, Set, Tuple

from tc_sim import utils
from .gate import Gate, GateType, NodeValue
from .circuit import Circuit, build_circuit_from_ECE6140_netlist, node_values_to_str
from .fault import SSAFault, read_fault_file


class PODEMGeneration:
    """
    PODEM algorithm implementation for test pattern generation.
    
    This class implements the core PODEM algorithm which generates test patterns
    to detect specific stuck-at faults. The algorithm uses recursive backtracking
    to systematically search the input space.
    
    Key concepts:
    - D-frontier: Gates with unknown output but at least one D/D' input
    - Objective: A (gate, value) pair to achieve
    - Backtrace: Finding a primary input to set to achieve an objective
    - Implication: Propagating values after setting an input
    
    Attributes:
        circuit: The circuit under test
        fault: The fault to generate a test for
    """
    def __init__(self, circuit: Circuit, fault: SSAFault):
        """
        Initialize PODEM generation for a specific fault.
        
        Args:
            circuit: The circuit to generate test patterns for
            fault: The stuck-at fault to detect
        """
        self.circuit: Circuit = circuit
        self.fault: SSAFault = fault

    def get_D_frontier(self) -> List[Gate]:
        """
        Get the D-frontier: gates with unknown output but at least one D/D' input.
        
        The D-frontier represents gates where the fault effect (D or D') can
        potentially be propagated forward toward a primary output. These are
        critical points for fault propagation.
        
        Returns:
            List of gates in the D-frontier
        """
        d_frontier = []
        for gate in self.circuit.gates.values():
            if gate.is_in_D_frontier():
                d_frontier.append(gate)
        return d_frontier

    def select_a_gate_from_D_frontier(self, d_frontier: List[Gate]) -> Gate:
        """
        Select a gate from the D-frontier for fault propagation.
        
        This implementation uses a simple strategy: select the first gate.
        More sophisticated implementations might use heuristics to select
        the most promising gate for faster convergence.
        
        Args:
            d_frontier: List of gates in the D-frontier
            
        Returns:
            The selected gate from the D-frontier
        """
        # Simple strategy: select the first gate
        # Could be improved with heuristics (e.g., prefer gates closer to outputs)
        return d_frontier[0]

    def select_a_input_node_from_d_frontier_gate(self, d_frontier_gate: Gate) -> Gate:
        """
        Select an unknown input node from a D-frontier gate.
        
        For fault propagation, we need to set unknown inputs to the
        non-controlling value to allow the D/D' value to propagate through.
        
        Args:
            d_frontier_gate: A gate from the D-frontier
            
        Returns:
            The fan-in gate corresponding to an unknown input
            
        Raises:
            AssertionError: If no unknown input is found (shouldn't happen)
        """
        for i, input_value in enumerate(d_frontier_gate.input_values):
            if input_value == NodeValue.UNKNOWN:
                fan_in_gate = d_frontier_gate.get_fan_in_gate_by_index(i)
                assert fan_in_gate.is_unknown(), "The fan-in gate should be unknown"
                return fan_in_gate
        assert False, "No unknown input value found in the D frontier gate"

    def select_a_input_node_from_backtrace_gate(self, backtrace_gate: Gate) -> Gate:
        """
        Select an unknown input node from a gate during backtrace.
        
        During backtrace, we work backward from an objective to find a primary
        input to set. This function selects one of the unknown inputs to continue
        the backtrace.
        
        Args:
            backtrace_gate: The current gate in the backtrace process
            
        Returns:
            The fan-in gate corresponding to an unknown input
            
        Raises:
            AssertionError: If no unknown input is found
        """
        for i, input_value in enumerate(backtrace_gate.input_values):
            if input_value == NodeValue.UNKNOWN:
                fan_in_gate = backtrace_gate.get_fan_in_gate_by_index(i)
                assert fan_in_gate.is_unknown(), "The fan-in gate should be unknown"
                return fan_in_gate
        assert False, "No unknown input value found in the backtrace gate" 
        

    def get_objective(self) -> Tuple[Gate, NodeValue]:
        """
        Determine the next objective: a (gate, value) pair to achieve.
        
        The objective selection follows this priority:
        1. If fault not activated: activate it (set fault site to activation value)
        2. If fault activated: propagate it (set D-frontier gate input to non-controlling value)
        
        If no D-frontier exists and fault is activated, the fault may be undetectable
        with the current assignments.
        
        Returns:
            A tuple (gate, value) representing the objective, or (None, None) if
            no objective can be determined (likely undetectable fault)
        """
        fault_backward_gate = self.fault.get_backward_gate()
        
        # Phase 1: Fault activation
        # If the fault site hasn't been set yet, make that the objective
        if fault_backward_gate.is_unknown():
            return (fault_backward_gate, self.fault.get_activation_value())
        
        # Phase 2: Fault propagation
        # Fault is activated, now we need to propagate it to an output
        else:
            d_frontier = self.get_D_frontier()
            
            # No D-frontier means fault cannot be propagated further
            if len(d_frontier) == 0:
                return (None, None)
            
            # Select a gate from D-frontier and an unknown input
            selected_gate = self.select_a_gate_from_D_frontier(d_frontier)
            selected_input_node = self.select_a_input_node_from_d_frontier_gate(selected_gate)
            
            # Objective: set input to non-controlling value to allow D/D' to propagate
            non_controlling_value = selected_gate.get_non_controlling_value()
            if non_controlling_value == NodeValue.UNKNOWN:
                # Default to ZERO if non-controlling value is not well-defined
                non_controlling_value = NodeValue.ZERO
            
            return (selected_input_node, non_controlling_value)

    def backtrace(self, objective: Tuple[Gate, NodeValue]) -> Tuple[Gate, NodeValue]:
        """
        Trace backward from an objective to find a primary input assignment.
        
        The backtrace process works backward through the circuit from an internal
        gate objective to a primary input, determining what value should be set
        at the input to achieve the objective.
        
        The value is inverted when passing through inverting gates (NOT, NAND, NOR, etc.).
        
        Args:
            objective: A (gate, value) pair representing the desired objective
            
        Returns:
            A tuple (input_gate, value) where input_gate is a primary input and
            value is the value to set it to
        """
        current_gate = objective[0]
        current_value = objective[1]
        
        # Trace backward until we reach a primary input
        while current_gate.type != GateType.INPUT:
            # Account for inversion if the gate is an inverting gate
            inversion_value = NodeValue.ONE if current_gate.is_inversion_gate() else NodeValue.ZERO
            current_value = current_value ^ inversion_value
            
            # Move to one of the fan-in gates
            current_gate = self.select_a_input_node_from_backtrace_gate(current_gate)
        
        return (current_gate, current_value)


    def circuit_imply(self, objective: Tuple[Gate, NodeValue]):
        """
        Set a primary input and propagate values through the circuit.
        
        This is the "implication" step where we assign a value to a primary input
        and evaluate the circuit (with the fault) to see the effects.
        
        Args:
            objective: A tuple (input_gate, value) where input_gate must be
                      a primary input and value is the value to assign
        """
        assert objective[0].type == GateType.INPUT, "The objective should be an input node"
        objective_value = objective[1]
        
        # Set the input value
        self.circuit.set_input_value(objective[0].name, objective_value)
        
        # Evaluate circuit with the fault injected
        self.circuit.evaluate_with_fault(self.fault)

    def check_fault_propagation(self, d_frontier_gate: Gate) -> bool:
        """
        Recursively check if there's a propagation path from a gate to any output.
        
        This function checks whether a gate with D/D' value (or in the D-frontier)
        can potentially propagate that fault effect to a primary output through
        unknown gates.
        
        Args:
            d_frontier_gate: Gate to check for propagation paths
            
        Returns:
            True if there exists a path to an output, False otherwise
        """
        # If gate has a known value, the path is blocked
        if not d_frontier_gate.is_unknown():
            return False
        
        # Reached a primary output - propagation is possible
        if d_frontier_gate.type == GateType.OUTPUT:
            return True
        
        # Recursively check fan-out gates
        for fan_out_gate in d_frontier_gate.fan_out_gates:
            if self.check_fault_propagation(fan_out_gate):
                return True
        
        # No path found to any output
        return False

    def check_all_fault_propagation(self) -> bool:
        """
        Check if fault propagation to an output is still possible.
        
        This function checks whether the fault effect can potentially reach
        any primary output given the current assignments. If not, we can
        prune this branch of the search tree early.
        
        Returns:
            True if propagation is still possible, False if it's blocked
        """
        # Check if any gate in the D-frontier can propagate to an output
        d_frontier = self.get_D_frontier()
        for d_frontier_gate in d_frontier:
            if self.check_fault_propagation(d_frontier_gate):
                return True
        
        # Also check from the fault site itself
        if self.check_fault_propagation(self.fault.get_backward_gate()):
            return True
        
        return False

    def is_successful(self) -> bool:
        """
        Check if the fault has been successfully detected at a primary output.
        
        Success means at least one primary output has value D or D', indicating
        that the fault effect has propagated to an observable point.
        
        Returns:
            True if fault is detected at an output, False otherwise
        """
        for output_gate in self.circuit.get_output_gates():
            if output_gate.output_value in (NodeValue.D, NodeValue.D_BAR):
                return True
        return False


    def pedem_recursive_body(self, depth: int = 0) -> bool:
        """
        Recursive core of the PODEM algorithm with backtracking.
        
        This function implements the recursive search with backtracking:
        1. Check if successful (fault detected at output)
        2. Check if propagation is still possible (early pruning)
        3. Get an objective (what to achieve next)
        4. Backtrace to find input assignment
        5. Try the assignment (recursive call)
        6. If fails, try the opposite value (backtrack)
        7. If both fail, undo the assignment and return failure
        
        Args:
            depth: Current recursion depth (for debugging/visualization)
            
        Returns:
            True if a test pattern was found, False otherwise
        """
        # Uncomment for debugging: visualize recursion depth
        # depth_str = "    " * depth
        # print(depth_str + "podem recursive body")
        
        # Success condition: fault detected at a primary output
        if self.is_successful():
            # print(depth_str + "is successful")
            return True

        # Pruning: check if fault propagation is still possible
        # print(depth_str + "circuit state: " + self.circuit.get_state_string())
        if not self.check_all_fault_propagation():
            # print(depth_str + "not all fault propagation")
            return False

        # Get the next objective
        objective = self.get_objective()
        # print(depth_str + "objective: " + objective[0].name + " " + str(objective[1]))
        
        # No valid objective means fault is undetectable with current assignments
        if objective[0] is None:
            return False

        # Backtrace to find primary input assignment
        input_objective = self.backtrace(objective)
        # print(depth_str + "input_objective: " + input_objective[0].name + " " + str(input_objective[1]))
        
        # Try the backtraced value
        self.circuit_imply(input_objective)
        if self.pedem_recursive_body(depth + 1):
            return True

        # Backtrack: try the opposite value
        input_objective = (input_objective[0], ~input_objective[1])
        # print(depth_str + "input_objective: " + input_objective[0].name + " " + str(input_objective[1]))
        self.circuit_imply(input_objective)
        if self.pedem_recursive_body(depth + 1):
            return True

        # Both values failed: reset this input to unknown and return failure
        input_objective = (input_objective[0], NodeValue.UNKNOWN)
        self.circuit_imply(input_objective)
        return False

    def run(self) -> bool:
        """
        Run the PODEM algorithm to generate a test pattern for the fault.
        
        Returns:
            True if a test pattern was successfully generated, False if the
            fault is undetectable
        """
        return self.pedem_recursive_body()

    def get_inputs(self) -> list[NodeValue]:
        """
        Get the current values of all primary inputs.
        
        Returns:
            List of NodeValue objects for each primary input
        """
        inputs = []
        for input_name in self.circuit.input_port_names:
            input_gate = self.circuit.gates[input_name]
            inputs.append(input_gate.output_value)
        return inputs

    def get_outputs(self) -> list[NodeValue]:
        """
        Get the current values of all primary outputs.
        
        Returns:
            List of NodeValue objects for each primary output
        """
        outputs = []
        for output_name in self.circuit.output_port_names:
            output_gate = self.circuit.gates[output_name]
            outputs.append(output_gate.output_value)
        return outputs


class PODEMWrapper:
    """
    Wrapper class for running PODEM on multiple faults and managing results.
    
    This class provides a convenient interface for:
    - Loading a circuit from a netlist file
    - Loading faults from a fault file
    - Running PODEM on all faults
    - Saving test patterns to files
    
    Attributes:
        circuit: The circuit loaded from the netlist
        faults: List of faults to generate tests for
        test_patterns: Generated test patterns (one per fault)
    """
    def __init__(self, circuit_file: str):
        """
        Initialize the PODEM wrapper with a circuit file.
        
        Args:
            circuit_file: Path to the circuit netlist file
        """
        self.circuit = build_circuit_from_ECE6140_netlist(circuit_file)
        self.faults = []
        self.test_patterns = []

    def run(self, fault: SSAFault) -> list[NodeValue]:
        """
        Run PODEM to generate a test pattern for a specific fault.
        
        This method:
        1. Resets the circuit to clear previous assignments
        2. Runs PODEM for the given fault
        3. Extracts the input pattern
        4. Converts D/D' values to 1/0 for practical testing
        
        Args:
            fault: The stuck-at fault to generate a test for
            
        Returns:
            List of NodeValue objects representing the test pattern
            (D and D' are converted to ONE and ZERO respectively)
        """
        # Reset circuit state from previous runs
        self.circuit.reset_gates()
        
        # Run PODEM algorithm
        self.podem = PODEMGeneration(self.circuit, fault)
        self.podem.run()
        
        # Extract test pattern from primary inputs
        test_pattern = self.podem.get_inputs()
        
        # Convert D-algebra values to binary values for actual testing
        # D → 1, D' → 0 (fault-free values)
        for i, input_value in enumerate(test_pattern):
            if input_value == NodeValue.D:
                test_pattern[i] = NodeValue.ONE
            elif input_value == NodeValue.D_BAR:
                test_pattern[i] = NodeValue.ZERO
        
        return test_pattern

    def add_faults_from_file(self, fault_file: str):
        """
        Load faults from a fault list file.
        
        Args:
            fault_file: Path to the fault list file
        """
        fault_pairs = read_fault_file(fault_file)
        for fault_pair in fault_pairs:
            self.faults.append(self.circuit.get_a_ssa_fault(*fault_pair))

    def run_all_faults(self) -> list[list[NodeValue]]:
        """
        Generate test patterns for all loaded faults.
        
        Returns:
            List of test patterns, one for each fault
        """
        self.test_patterns = []
        for fault in self.faults:
            test_pattern = self.run(fault)
            self.test_patterns.append(test_pattern)
        return self.test_patterns

    def get_all_faults(self) -> list[SSAFault]:
        """
        Get the list of all loaded faults.
        
        Returns:
            List of SSAFault objects
        """
        return self.faults

    def save_test_patterns_verbose(self, file_path: str):
        """
        Save test patterns to a file with verbose output (includes fault information).
        
        Each line contains: "fault_description: test_pattern"
        Undetectable faults (all X values) are shown with underscores.
        
        Args:
            file_path: Path to the output file
        """
        directory, file_name_without_extension, extension = utils.prepare_output_file(file_path)
        file_path = os.path.join(directory, f"{file_name_without_extension}{extension}")
        
        with open(file_path, 'w') as file:
            for fault, test_pattern in zip(self.faults, self.test_patterns):
                fault_str = fault.get_formatted_string()
                test_pattern_str = node_values_to_str(test_pattern)
                
                # Mark undetectable faults with underscores
                if "1" not in test_pattern_str and "0" not in test_pattern_str:
                    test_pattern_str = "_" * len(test_pattern_str)
                
                file.write(fault_str + ": " + test_pattern_str + '\n')
        
        print(f"Test patterns have been saved to {file_path}")

    def save_test_patterns(self, file_path: str):
        """
        Save test patterns to a file (test patterns only, no fault info).
        
        Each line contains just the test pattern.
        Undetectable faults (all X values) are shown with underscores.
        
        Args:
            file_path: Path to the output file
        """
        directory, file_name_without_extension, extension = utils.prepare_output_file(file_path)
        file_path = os.path.join(directory, f"{file_name_without_extension}{extension}")
        
        with open(file_path, 'w') as file:
            for fault, test_pattern in zip(self.faults, self.test_patterns):
                test_pattern_str = node_values_to_str(test_pattern)
                
                # Mark undetectable faults with underscores
                if "1" not in test_pattern_str and "0" not in test_pattern_str:
                    test_pattern_str = "_" * len(test_pattern_str)
                
                file.write(test_pattern_str + '\n')
        
        print(f"Test patterns have been saved to {file_path}")