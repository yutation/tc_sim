import os
import re
from typing import List, Set, Tuple

from tc_sim import utils
from .gate import Gate, GateType, NodeValue
from .circuit import Circuit, build_circuit_from_ECE6140_netlist, node_values_to_str
from .fault import SSAFault, read_fault_file




class PODEMGeneration:
    def __init__(self, circuit: Circuit, fault: SSAFault):
        self.circuit: Circuit = circuit
        self.fault: SSAFault = fault

    def get_D_frontier(self) -> Set[Gate]:
        D_frontier = []
        for gate in self.circuit.gates.values():
            if gate.is_in_D_frontier():
                D_frontier.append(gate)
        return D_frontier

    
    def select_a_gate_from_D_frontier(self, d_frontier: List[Gate]) -> Gate:
        # Select a gate.
        # The first one for the sake of simplicity.
        return d_frontier[0]

    def select_a_input_node_from_d_frontier_gate(self, d_frontier_gate: Gate) -> Gate:
        for i, input_value in enumerate(d_frontier_gate.input_values):
            if input_value == NodeValue.UNKNOWN:
                fan_in_gate = d_frontier_gate.get_fan_in_gate_by_index(i)
                assert fan_in_gate.is_unknown(), "The fan-in gate should be unknown"
                return fan_in_gate
        assert False, "No unknown input value found in the D frontier gate"

    def select_a_input_node_from_backtrace_gate(self, backtrace_gate: Gate) -> Gate:
        for i, input_value in enumerate(backtrace_gate.input_values):
            if input_value == NodeValue.UNKNOWN:
                fan_in_gate = backtrace_gate.get_fan_in_gate_by_index(i)
                assert fan_in_gate.is_unknown(), "The fan-in gate should be unknown"
                return fan_in_gate
        assert False, "No unknown input value found in the backtrace gate" 
        

    
    def get_objective(self) -> Tuple[Gate, NodeValue]:
        fault_backward_gate = self.fault.get_backward_gate()
        if fault_backward_gate.is_unknown():
            return (fault_backward_gate, self.fault.get_activation_value())
        else:
            d_frontier = self.get_D_frontier()
            if len(d_frontier) == 0:
                return (None, None)
            selected_gate = self.select_a_gate_from_D_frontier(d_frontier)
            selected_input_node = self.select_a_input_node_from_d_frontier_gate(selected_gate)
            non_controlling_value = selected_gate.get_non_controlling_value()
            if non_controlling_value == NodeValue.UNKNOWN:
                non_controlling_value = NodeValue.ZERO
            return (selected_input_node, non_controlling_value)


    def backtrace(self, objective: Tuple[Gate, NodeValue]) -> Tuple[Gate, NodeValue]:
        current_gate = objective[0]
        current_value = objective[1]
        while current_gate.type != GateType.INPUT:
            inversion_value = NodeValue.ONE if current_gate.is_inversion_gate() else NodeValue.ZERO
            current_value = current_value ^ inversion_value
            current_gate = self.select_a_input_node_from_backtrace_gate(current_gate)
        return (current_gate, current_value)


    def circuit_imply(self, objective: Tuple[Gate, NodeValue]) -> bool:
        assert objective[0].type == GateType.INPUT, "The objective should be an input node"
        objective_value = objective[1]
        self.circuit.set_input_value(objective[0].name, objective_value)
        self.circuit.evaluate_with_fault(self.fault)

    
    def check_fault_propagation(self, d_frontier_gate: Gate) -> bool:
        # print("check_fault_propagation: " + d_frontier_gate.name)
        if d_frontier_gate.is_unknown():
            if d_frontier_gate.type == GateType.OUTPUT:
                return True
            else:
                for fan_out_gate in d_frontier_gate.fan_out_gates:
                    if self.check_fault_propagation(fan_out_gate):
                        return True
                return False
        else:
            return False

    def check_all_fault_propagation(self) -> bool:
        d_frontier = self.get_D_frontier()
        for d_frontier_gate in d_frontier:
            if self.check_fault_propagation(d_frontier_gate):
                return True
        if self.check_fault_propagation(self.fault.get_backward_gate()):
            return True
        return False

    
    def is_successful(self) -> bool:
        for output_gate in self.circuit.get_output_gates():
            if output_gate.output_value == NodeValue.D or output_gate.output_value == NodeValue.D_BAR:
                return True
        return False


    def pedem_recursive_body(self, depth: int = 0) -> bool:
        depth_str = "    " * depth
        # print(depth_str + "pedmem recursive body")
        if self.is_successful():
            # print(depth_str + "is successful")
            return True

        # print(depth_str + "circuit state: " + self.circuit.get_state_string())
        if not self.check_all_fault_propagation():
            # print(depth_str + "not all fault propagation")
            return False

        objective = self.get_objective()
        # print(depth_str + "objective: " + objective[0].name + " " + str(objective[1]))
        if objective[0] is None:
            return False

        input_objective = self.backtrace(objective)
        # print(depth_str + "input_objective: " + input_objective[0].name + " " + str(input_objective[1]))
        self.circuit_imply(input_objective)
        if self.pedem_recursive_body(depth + 1):
            return True


        input_objective = (input_objective[0], ~input_objective[1])
        # print(depth_str + "input_objective: " + input_objective[0].name + " " + str(input_objective[1]))
        self.circuit_imply(input_objective)
        if self.pedem_recursive_body(depth + 1):
            return True

        input_objective = (input_objective[0], NodeValue.UNKNOWN)
        self.circuit_imply(input_objective)
        return False
            

    def run(self) -> bool:
        return self.pedem_recursive_body()

    
    def get_inputs(self) -> list[NodeValue]:
        inputs = []
        for input_name in self.circuit.input_port_names:
            input_gate = self.circuit.gates[input_name]
            inputs.append(input_gate.output_value)
        return inputs

    def get_outputs(self) -> list[NodeValue]:
        outputs = []
        for output_name in self.circuit.output_port_names:
            output_gate = self.circuit.gates[output_name]
            outputs.append(output_gate.output_value)
        return outputs


class PODEMWrapper:
    def __init__(self, circuit_file: str):
        self.circuit = build_circuit_from_ECE6140_netlist(circuit_file)
        self.faults = []
        self.test_patterns = []

    def run(self, fault: SSAFault) -> list[NodeValue]:
        self.circuit.reset_gates()
        self.podem = PODEMGeneration(self.circuit, fault)
        self.podem.run()
        test_pattern = self.podem.get_inputs()
        for i, input_value in enumerate(test_pattern):
            if input_value == NodeValue.D:
                test_pattern[i] = NodeValue.ONE
            elif input_value == NodeValue.D_BAR:
                test_pattern[i] = NodeValue.ZERO
        return test_pattern

    def add_faults_from_file(self, fault_file: str):
        fault_pairs = read_fault_file(fault_file)
        for fault_pair in fault_pairs:
            self.faults.append(self.circuit.get_a_ssa_fault(*fault_pair))

    def run_all_faults(self) -> list[list[NodeValue]]:
        self.test_patterns = []
        for fault in self.faults:
            test_pattern = self.run(fault)
            self.test_patterns.append(test_pattern)
        return self.test_patterns

    def get_all_faults(self) -> list[SSAFault]:
        return self.faults

    def save_test_patterns(self, file_path: str):
        directory, file_name_without_extension, extension = utils.prepare_output_file(file_path)
        file_path = os.path.join(directory, f"{file_name_without_extension}{extension}")
        with open(file_path, 'w') as file:
            for fault, test_pattern in zip(self.faults, self.test_patterns):
                fault_str = fault.get_formatted_string()
                test_pattern_str = node_values_to_str(test_pattern)
                if "1" not in test_pattern_str and "0" not in test_pattern_str:
                    test_pattern_str = "_"*len(test_pattern_str)
                file.write(fault_str + ": " + test_pattern_str + '\n')
        print(f"Test patterns have been saved to {file_path}")