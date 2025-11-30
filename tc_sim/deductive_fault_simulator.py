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
    def __init__(self, fault_set: set[SSAFault] = set(), valid: bool = False):
        self.fault_set = fault_set
        self.valid = valid
    def __str__(self):
        return f"DeductiveInfo({self.fault_set}, {self.valid})"
    def __repr__(self):
        return f"DeductiveInfo({self.fault_set}, {self.valid})"


class DeductiveFaultSimulator:
    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        assert self.circuit.evaluated, "Circuit must be evaluated before running deductive fault simulator"
        self.all_fault_set = self.get_all_faults()
        # Pre-compute control values for faster lookup
        self._control_values = {
            GateType.AND: NodeValue.ZERO,
            GateType.NAND: NodeValue.ZERO,
            GateType.OR: NodeValue.ONE,
            GateType.NOR: NodeValue.ONE
        }

    def get_all_faults(self):
        all_fault_set = set()
        for w in self.circuit.wires.values():
            # param = {"wire": w, "forward_gates": w.output_gates, "backward_gate": w.input_gate}
            all_fault_set.add(SSAFault(w.name, NodeValue.ONE))
            all_fault_set.add(SSAFault(w.name, NodeValue.ZERO))
        return all_fault_set


    def gate_deductive_eval(self, eval_gate: Gate, input_value_list: List[NodeValue], input_set_list: List[Set[SSAFault]]) -> Set[SSAFault]:
        output_wire = eval_gate.fan_out_wire
        gate_type = eval_gate.type
        gate_output_value = eval_gate.output_value
        result_fault_set: Set[SSAFault] = set()
        
        # Output gate have no output wire, so we don't need to create an output fault
        if gate_type != GateType.OUTPUT:
            output_fault = SSAFault(output_wire.name, ~gate_output_value)

        if gate_type == GateType.OUTPUT:
            assert len(input_set_list) == 1, "Output gate should have one input set list"
            result_fault_set = input_set_list[0]
        elif gate_type == GateType.INPUT:
            assert len(input_set_list) == 0, "Input gate should have no input set list"
            if gate_output_value != NodeValue.UNKNOWN:
                result_fault_set.add(output_fault)
        elif gate_type in [GateType.NOT, GateType.BUF]:
            assert len(input_set_list) == 1, "NOT or BUF gate should have one input set list"
            if gate_output_value != NodeValue.UNKNOWN:
                result_fault_set = input_set_list[0] | {output_fault}
            else:
                result_fault_set = input_set_list[0]
        elif gate_type in [GateType.AND, GateType.OR, GateType.NAND, GateType.NOR]:
            # Use pre-computed control value for faster lookup
            control_value = self._control_values.get(gate_type, NodeValue.UNKNOWN)
            uc_set: Set[SSAFault] = set()
            c_set = self.all_fault_set.copy()  # Use copy() instead of deepcopy for better performance
            have_control = False
            x_count = 0

            for input_value, input_set in zip(input_value_list, input_set_list):
                if input_value == control_value:
                    have_control = True
                    c_set &= input_set  # Use &= operator for in-place intersection
                elif input_value == ~control_value:
                    uc_set |= input_set  # Use |= operator for in-place union
                elif input_value == NodeValue.UNKNOWN:
                    x_count += 1
                else:
                    raise ValueError(f"Invalid input value {input_value}")
            if x_count == 0:
                if have_control:
                    result_fault_set = (c_set - uc_set) | {output_fault}
                else:
                    result_fault_set = uc_set | {output_fault}
            elif have_control:
                    result_fault_set = {output_fault}
        elif gate_type in [GateType.XOR, GateType.XNOR]:
            c_set: Set[SSAFault] = set()
            for input_value, input_set in zip(input_value_list, input_set_list):
                if input_value == NodeValue.UNKNOWN:
                    x_count += 1
                c_set ^= input_set  # Use ^= operator for in-place XOR
            if x_count == 0:
                result_fault_set = c_set | {output_fault}
        else:
            raise ValueError(f"Invalid gate type {gate_type}")
            
        return result_fault_set

    def deductive_eval(self):
        evaluation_queue = deque()
        # Pre-allocate sets to avoid repeated allocation
        final_fault_set: Set[SSAFault] = set()
        deductive_info_dict: Dict[str, DeductiveInfo] = {}
        
        def add_fan_out_gates_to_queue(gate: Gate):
            # Use extend for better performance than multiple appends
            evaluation_queue.extend(gate.fan_out_gates)
            
        # Initialize queue with input gates
        for input_port_name in self.circuit.input_port_names:
            input_port_gate = self.circuit.gates[input_port_name]
            evaluation_queue.append(input_port_gate)

        while evaluation_queue:
            # print("queue: ", [gate.name for gate in evaluation_queue])
            current_gate: Gate = evaluation_queue.popleft()
            
            # Assert that each gate is evaluated exactly once
            if current_gate.name in deductive_info_dict:
                continue
            # print("current_gate: ", current_gate.name)
            # print("deductive_info_dict: ", deductive_info_dict.keys())
            # assert current_gate.name not in deductive_info_dict, f"Gate {current_gate.name} is being evaluated multiple times - this violates the algorithm"
            
            if current_gate.type == GateType.INPUT:
                result_fault_set = self.gate_deductive_eval(current_gate, [], [])
                deductive_info_dict[current_gate.name] = DeductiveInfo(result_fault_set, True)
                add_fan_out_gates_to_queue(current_gate)
            elif current_gate.type == GateType.OUTPUT:
                fan_in_gate = current_gate.fan_in_gates[0]
                input_set = deductive_info_dict[fan_in_gate.name].fault_set
                input_value = fan_in_gate.output_value
                result_fault_set = self.gate_deductive_eval(current_gate, [input_value], [input_set])
                deductive_info_dict[current_gate.name] = DeductiveInfo(result_fault_set, True)
                final_fault_set |= result_fault_set  # Use |= for in-place union
            else:
                # Pre-allocate list with known size
                input_set_list: List[Set[SSAFault]] = []
                ready_to_eval = True
                
                for fan_in_gate in current_gate.fan_in_gates:
                    if fan_in_gate.name not in deductive_info_dict:
                        ready_to_eval = False
                        break
                    input_set_list.append(deductive_info_dict[fan_in_gate.name].fault_set)
                    
                if not ready_to_eval:
                    continue
                    
                # Use list comprehension for better performance
                input_value_list = [gate.output_value for gate in current_gate.fan_in_gates]
                result_fault_set = self.gate_deductive_eval(current_gate, input_value_list, input_set_list)
                deductive_info_dict[current_gate.name] = DeductiveInfo(result_fault_set, True)
                add_fan_out_gates_to_queue(current_gate)
                
        return final_fault_set


class DFSWrapper():
    def __init__(self, circuit_file: str, fault_set_file: Optional[str] = None):
        self.circuit = cc.build_circuit_from_ECE6140_netlist(circuit_file)
        self.circuit_file = circuit_file
        self.fault_set_file = fault_set_file
        self.test_pattern_str_list = []
        self.all_fault_set = self.parse_fault_set_file(fault_set_file) if fault_set_file is not None else None
        self.found_fault_set_list = []

    
    def add_test_pattern_from_file(self, test_pattern_file: str):
        self.test_pattern_str_list.extend(self.parse_test_pattern_file(test_pattern_file))
        
    def parse_fault_set_file(self, fault_set_file: str) -> Set[SSAFault]:
        fault_pairs = ft.read_fault_file(fault_set_file)
        fault_set = set()
        for node_name, fault_value in fault_pairs:
            fault_set.add(SSAFault(node_name, fault_value))
        return fault_set

    def parse_test_pattern_file(self, test_pattern_file: str) -> List[str]:
        test_pattern_list = []
        with open(test_pattern_file, 'r') as file:
            for line in file:
                line = line.strip()
                test_pattern_list.append(line)
        return test_pattern_list

    def run(self, input_values: str) -> List[SSAFault]:
        self.str_input_values = input_values
        input_node_values = cc.str_inputs_to_node_values(input_values)
        
        self.circuit.reset_gates()
        self.circuit.set_inputs(input_node_values)
        self.circuit.evaluate()
        
        # Create new simulator for each evaluation to ensure clean state
        deductive_fault_simulator = DeductiveFaultSimulator(self.circuit)
        final_fault_set = deductive_fault_simulator.deductive_eval()
        
        if self.all_fault_set is not None:
            final_fault_set &= self.all_fault_set  # Use &= for in-place intersection
            
        sorted_final_fault_set = ft.sort_ssa_faults_by_node_name(list(final_fault_set))
        return sorted_final_fault_set

    def run_all_test_patterns(self):
        self.found_fault_set_list = []
        for test_pattern_str in self.test_pattern_str_list:
            found_fault_set = self.run(test_pattern_str)
            self.found_fault_set_list.append(found_fault_set)
        return self.found_fault_set_list

    def save_detected_fault_set(self, detected_fault_set:List[SSAFault], input_values: str, output_file: str):
        with open(output_file, 'w') as file:
            file.write(f"Circuit file: {self.circuit_file}\n")
            file.write(f"Fault set file: {self.fault_set_file}\n")
            file.write(f"Input values: {input_values}\n")
            file.write(f"Detected faults: {len(detected_fault_set)}\n")
            file.write(f"------FAULTS DETECTED------\n")
            for fault in detected_fault_set:
                node_name = fault.node_name
                digit_fault_value = 0 if fault.fault_value == NodeValue.ZERO else 1 if fault.fault_value == NodeValue.ONE else 2
                str = f"{node_name} stuck at {digit_fault_value}"
                file.write(str + '\n')
        print(f"Detected faults have been saved to {output_file}")

    def save_detected_fault_set_v2(self, detected_fault_set:List[SSAFault], input_values: str, output_file1: str, output_file2: str):
        with open(output_file1, 'w') as file:
            file.write(f"Circuit file: {self.circuit_file}\n")
            file.write(f"Fault set file: {self.fault_set_file}\n")
            file.write(f"Input values: {input_values}\n")
            file.write(f"Detected faults: {len(detected_fault_set)}\n")
            file.write(f"------FAULTS DETECTED------\n")
        with open(output_file2, 'w') as file:
            for fault in detected_fault_set:
                node_name = fault.node_name
                digit_fault_value = 0 if fault.fault_value == NodeValue.ZERO else 1 if fault.fault_value == NodeValue.ONE else 2
                str = f"{node_name} stuck at {digit_fault_value}"
                file.write(str + '\n')
        print(f"Detected faults have been saved to {output_file1} and {output_file2}")


    def save_detected_fault_set_list(self, file_path: str):
        directory, file_name_without_extension, extension = utils.prepare_output_file(file_path)
        for i, detected_fault_set in enumerate(self.found_fault_set_list):
            output_file = os.path.join(directory, f"{file_name_without_extension}_{i}{extension}")
            self.save_detected_fault_set(detected_fault_set, self.test_pattern_str_list[i], output_file)
        # print(f"Detected faults have been saved to {file_path}")


        
        
