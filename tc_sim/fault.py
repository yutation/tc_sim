from typing import List, Tuple
from .gate import NodeValue, Gate, Wire

class SSAFault():
    def __init__(self, node_name, fault_value: NodeValue, parameters: dict = {}):
        self.node_name = node_name
        self.fault_value = fault_value
        self.correct_value = fault_value.__invert__()
        self.activation_value = fault_value.__invert__()
        self.d_value = NodeValue.D if fault_value == NodeValue.ZERO else NodeValue.D_BAR if fault_value == NodeValue.ONE else NodeValue.UNKNOWN
        self.parameters = parameters
        self.wire:Wire = parameters.get('wire', None)
        if self.wire is not None:
            self.backward_gate = self.wire.input_gate
            self.forward_gates = self.wire.output_gates
        else:
            self.backward_gate:Gate = parameters.get('backward_gate', None)
            self.forward_gates:list[Gate] = parameters.get('forward_gates', [])


    def get_backward_gate(self) -> Gate:
        return self.backward_gate

    def get_activation_value(self) -> NodeValue:
        return self.activation_value

    def get_fault_d_value(self) -> NodeValue:
        return self.d_value

    def __eq__(self, other):
        if not isinstance(other, SSAFault):
            return False
        return self.node_name == other.node_name and self.fault_value == other.fault_value

    def __hash__(self):
        return hash((self.node_name, self.fault_value.value))

    def __str__(self):
        digit_fault_value = 0 if self.fault_value == NodeValue.ZERO else 1 if self.fault_value == NodeValue.ONE else 2
        return f"{self.node_name}/{digit_fault_value}"

    def __repr__(self):
        return f"SSAFault(node_name={self.node_name}, fault_value={self.fault_value})"

    def get_formatted_string(self) -> str:
        value_str = '0' if self.fault_value == NodeValue.ZERO else '1' if self.fault_value == NodeValue.ONE else 'X'
        return f"{self.node_name} stuck at {value_str}"
    
    


def sort_ssa_faults_by_node_name(faults: list[SSAFault]) -> list[SSAFault]:
    """
    Sort a list of SSAFault objects by their node_name in increasing order.
    The node_name is converted to int before sorting.
    
    Args:
        faults: List of SSAFault objects to sort
        
    Returns:
        Sorted list of SSAFault objects
    """
    return sorted(faults, key=lambda fault: int(fault.node_name))


def read_fault_file(fault_file: str) -> List[Tuple[str, NodeValue]]:
    fault_pairs = []
    with open(fault_file, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                # Parse format: "node_name stuck at value"
                # Example: "3 stuck at 0" or "5 stuck at 1"
                parts = line.split()
                if len(parts) == 4 and parts[1] == "stuck" and parts[2] == "at":
                    node_name = parts[0]
                    value_str = parts[3]
                    if value_str == "0":
                        fault_value = NodeValue.ZERO
                    elif value_str == "1":
                        fault_value = NodeValue.ONE
                    else:
                        continue  # Skip invalid fault values
                    fault_pairs.append((node_name, fault_value))
    return fault_pairs