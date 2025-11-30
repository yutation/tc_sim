"""
Fault models and utilities for fault simulation.

This module defines the Single Stuck-At (SSA) fault model and provides
utilities for reading fault files and managing fault lists.
"""

from typing import List, Tuple
from .gate import NodeValue, Gate, Wire


class SSAFault:
    """
    Single Stuck-At (SSA) Fault model.
    
    Represents a fault where a wire in the circuit is stuck at either 0 or 1,
    regardless of the actual circuit behavior. This is a classical fault model
    used in digital circuit testing.
    
    Attributes:
        node_name: Name of the wire/node that has the fault
        fault_value: The stuck-at value (ZERO or ONE)
        correct_value: The inverted fault value (expected good circuit value)
        activation_value: Value needed to activate (detect) the fault
        d_value: D-algebra value representing the fault (D or D')
        parameters: Additional parameters including wire and gate references
        wire: Reference to the Wire object (if provided)
        backward_gate: Gate that drives the faulty wire
        forward_gates: Gates that read from the faulty wire
    """
    
    def __init__(self, node_name: str, fault_value: NodeValue, parameters: dict = None):
        """
        Initialize a Single Stuck-At Fault.
        
        Args:
            node_name: Name of the node/wire with the fault
            fault_value: The stuck-at value (NodeValue.ZERO or NodeValue.ONE)
            parameters: Optional dictionary containing:
                - 'wire': Wire object reference
                - 'backward_gate': Gate driving the wire
                - 'forward_gates': List of gates reading from the wire
        """
        if parameters is None:
            parameters = {}
            
        self.node_name = node_name
        self.fault_value = fault_value
        
        # Derive related values from the fault value
        self.correct_value = fault_value.__invert__()  # Good circuit value
        self.activation_value = fault_value.__invert__()  # Value to activate fault
        
        # Map to D-algebra: stuck-at-0 → D, stuck-at-1 → D'
        if fault_value == NodeValue.ZERO:
            self.d_value = NodeValue.D
        elif fault_value == NodeValue.ONE:
            self.d_value = NodeValue.D_BAR
        else:
            self.d_value = NodeValue.UNKNOWN
        
        # Store parameters and extract wire/gate references
        self.parameters = parameters
        self.wire: Wire = parameters.get('wire', None)
        
        if self.wire is not None:
            # Extract gate references from the wire
            self.backward_gate = self.wire.input_gate
            self.forward_gates = self.wire.output_gates
        else:
            # Use explicitly provided gate references
            self.backward_gate: Gate = parameters.get('backward_gate', None)
            self.forward_gates: list[Gate] = parameters.get('forward_gates', [])


    def get_backward_gate(self) -> Gate:
        """
        Get the gate that drives the faulty wire.
        
        Returns:
            The backward (driving) gate
        """
        return self.backward_gate

    def get_activation_value(self) -> NodeValue:
        """
        Get the value needed to activate (detect) this fault.
        
        For a stuck-at-0 fault, we need the wire to be 1 in the good circuit.
        For a stuck-at-1 fault, we need the wire to be 0 in the good circuit.
        
        Returns:
            The activation value (opposite of the fault value)
        """
        return self.activation_value

    def get_fault_d_value(self) -> NodeValue:
        """
        Get the D-algebra value representing this fault.
        
        Returns:
            NodeValue.D for stuck-at-0, NodeValue.D_BAR for stuck-at-1
        """
        return self.d_value

    def __eq__(self, other) -> bool:
        """
        Check equality between two SSAFault objects.
        
        Two faults are equal if they affect the same node with the same fault value.
        
        Args:
            other: Another object to compare with
            
        Returns:
            True if faults are equal, False otherwise
        """
        if not isinstance(other, SSAFault):
            return False
        return self.node_name == other.node_name and self.fault_value == other.fault_value

    def __hash__(self) -> int:
        """
        Compute hash value for use in sets and dictionaries.
        
        Returns:
            Hash value based on node name and fault value
        """
        return hash((self.node_name, self.fault_value.value))

    def __str__(self) -> str:
        """
        Short string representation in format: node_name/fault_value.
        
        Example: "3/0" for node 3 stuck at 0
        
        Returns:
            Compact string representation
        """
        if self.fault_value == NodeValue.ZERO:
            digit_fault_value = 0
        elif self.fault_value == NodeValue.ONE:
            digit_fault_value = 1
        else:
            digit_fault_value = 2
        return f"{self.node_name}/{digit_fault_value}"

    def __repr__(self) -> str:
        """
        Detailed string representation for debugging.
        
        Returns:
            Full representation showing all attributes
        """
        return f"SSAFault(node_name={self.node_name}, fault_value={self.fault_value})"

    def get_formatted_string(self) -> str:
        """
        Get a human-readable formatted string for the fault.
        
        Example: "3 stuck at 0"
        
        Returns:
            Formatted string describing the fault
        """
        if self.fault_value == NodeValue.ZERO:
            value_str = '0'
        elif self.fault_value == NodeValue.ONE:
            value_str = '1'
        else:
            value_str = 'X'
        return f"{self.node_name} stuck at {value_str}"
    
    


def sort_ssa_faults_by_node_name(faults: list[SSAFault]) -> list[SSAFault]:
    """
    Sort a list of SSAFault objects by their node_name in increasing order.
    
    The node_name is converted to int before sorting to ensure numerical
    ordering rather than lexicographic ordering (e.g., 2 < 10, not "10" < "2").
    
    Args:
        faults: List of SSAFault objects to sort
        
    Returns:
        Sorted list of SSAFault objects in ascending node name order
        
    Example:
        >>> faults = [SSAFault("10", NodeValue.ZERO), SSAFault("2", NodeValue.ONE)]
        >>> sorted_faults = sort_ssa_faults_by_node_name(faults)
        >>> [f.node_name for f in sorted_faults]
        ["2", "10"]
    """
    return sorted(faults, key=lambda fault: int(fault.node_name))


def read_fault_file(fault_file: str) -> List[Tuple[str, NodeValue]]:
    """
    Read a fault list file and parse it into a list of (node_name, fault_value) tuples.
    
    The expected file format is:
        node_name stuck at value
    
    where:
    - node_name is a string identifier for the wire/node
    - value is either 0 or 1
    
    Lines that don't match this format are silently skipped.
    
    Args:
        fault_file: Path to the fault list file
        
    Returns:
        List of tuples, each containing (node_name, fault_value)
        
    Example file content:
        3 stuck at 0
        5 stuck at 1
        7 stuck at 0
        
    Example:
        >>> fault_pairs = read_fault_file("faults.txt")
        >>> fault_pairs
        [("3", NodeValue.ZERO), ("5", NodeValue.ONE), ("7", NodeValue.ZERO)]
    """
    fault_pairs = []
    
    with open(fault_file, 'r') as file:
        for line in file:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Parse format: "node_name stuck at value"
            # Example: "3 stuck at 0" or "5 stuck at 1"
            parts = line.split()
            
            # Validate format: exactly 4 parts with correct keywords
            if len(parts) == 4 and parts[1] == "stuck" and parts[2] == "at":
                node_name = parts[0]
                value_str = parts[3]
                
                # Map string value to NodeValue enum
                if value_str == "0":
                    fault_value = NodeValue.ZERO
                elif value_str == "1":
                    fault_value = NodeValue.ONE
                else:
                    # Skip invalid fault values
                    continue
                
                fault_pairs.append((node_name, fault_value))
    
    return fault_pairs