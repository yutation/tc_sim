"""
Gate module for digital circuit simulation.

This module provides gate type definitions, gate value logic (including D-algebra for
fault simulation), and implementations of various logic gates (AND, OR, NOT, XOR, etc.).
"""

from enum import Enum


class GateType(Enum):
    """
    Enumeration of supported gate types in the circuit simulator.
    
    Includes basic logic gates (AND, OR, NOT, XOR, etc.) and special gates
    for circuit I/O (INPUT, OUTPUT).
    """
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    XOR = "XOR"
    NAND = "NAND"
    NOR = "NOR"
    XNOR = "XNOR"
    BUF = "BUF"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def create_gate(self, gate_name: str, input_number: int):
        """
        Factory method to create a gate instance based on the gate type.
        
        Args:
            gate_name: Unique identifier for the gate
            input_number: Number of input connections for the gate
            
        Returns:
            A Gate subclass instance corresponding to this gate type
        """
        if self == GateType.AND:
            return ANDGate(gate_name, input_number)
        elif self == GateType.OR:
            return ORGate(gate_name, input_number)
        elif self == GateType.NOT:
            return NOTGate(gate_name, 1)  # NOT gate always has 1 input
        elif self == GateType.XOR:
            return XORGate(gate_name, input_number)
        elif self == GateType.NAND:
            return NANDGate(gate_name, input_number)
        elif self == GateType.NOR:
            return NORGate(gate_name, input_number)
        elif self == GateType.XNOR:
            return XNORGate(gate_name, input_number)
        elif self == GateType.BUF:
            return BUFGate(gate_name, 1)  # BUF gate always has 1 input
        elif self == GateType.INPUT:
            return INPUTGate(gate_name, 0)  # INPUT gate has no inputs
        elif self == GateType.OUTPUT:
            return OUTPUTGate(gate_name, 1)  # OUTPUT gate has 1 input


class NodeValue(Enum):
    """
    Five-valued logic system for gate simulation supporting fault testing.
    
    Values:
        ZERO: Logic 0
        ONE: Logic 1
        UNKNOWN: Unknown/uninitialized value (X)
        D: Faulty value that is 1 in the good circuit but 0 in the faulty circuit
        D_BAR: Faulty value that is 0 in the good circuit but 1 in the faulty circuit
        
    The D-algebra enables detection and propagation of faults through the circuit.
    """
    ZERO = "Zero"
    ONE = "One"
    UNKNOWN = "Unknown"
    D = "D_fault"
    D_BAR = "D_bar_fault"

    def __str__(self):
        """String representation of the gate value."""
        return self.value
    
    def __repr__(self):
        return self.value
    
    def __or__(self, other):
        """
        Five-valued OR logic operation.
        
        Implements OR operation for {0, 1, X, D, D'} value system following
        D-algebra rules for fault propagation.
        
        Args:
            other: Another GateValue to OR with
            
        Returns:
            Result of the OR operation
        """
        a, b = self, other

        # If either is ONE, result is ONE
        if a == NodeValue.ONE or b == NodeValue.ONE:
            return NodeValue.ONE

        # If both ZERO -> ZERO; if one ZERO -> other (including D / D')
        if a == NodeValue.ZERO and b == NodeValue.ZERO:
            return NodeValue.ZERO
        if a == NodeValue.ZERO:
            return b
        if b == NodeValue.ZERO:
            return a

        # Handle unknowns (x)
        if a == NodeValue.UNKNOWN or b == NodeValue.UNKNOWN:
            # x OR 1 handled above; otherwise x
            return NodeValue.UNKNOWN

        # Handle D-algebra combinations
        if a == NodeValue.D and b == NodeValue.D:
            return NodeValue.D
        if a == NodeValue.D_BAR and b == NodeValue.D_BAR:
            return NodeValue.D_BAR
        # D OR D' -> 1
        if {a, b} == {NodeValue.D, NodeValue.D_BAR}:
            return NodeValue.ONE

        # Fallback to unknown if any new value shows up
        return NodeValue.UNKNOWN
    
    def __and__(self, other):
        """
        Five-valued AND logic operation.
        
        Implements AND operation for {0, 1, X, D, D'} value system following
        D-algebra rules for fault propagation.
        
        Args:
            other: Another GateValue to AND with
            
        Returns:
            Result of the AND operation
        """
        a, b = self, other

        # If either is ZERO, result is ZERO
        if a == NodeValue.ZERO or b == NodeValue.ZERO:
            return NodeValue.ZERO

        # If both ONE -> ONE; if one ONE -> other
        if a == NodeValue.ONE and b == NodeValue.ONE:
            return NodeValue.ONE
        if a == NodeValue.ONE:
            return b
        if b == NodeValue.ONE:
            return a

        # Handle unknowns (x)
        if a == NodeValue.UNKNOWN or b == NodeValue.UNKNOWN:
            # 0 handled above; otherwise x
            return NodeValue.UNKNOWN

        # Handle D-algebra combinations
        if a == NodeValue.D and b == NodeValue.D:
            return NodeValue.D
        if a == NodeValue.D_BAR and b == NodeValue.D_BAR:
            return NodeValue.D_BAR
        # D AND D' -> 0
        if {a, b} == {NodeValue.D, NodeValue.D_BAR}:
            return NodeValue.ZERO

        # Fallback to unknown for any unhandled case
        return NodeValue.UNKNOWN

    def __xor__(self, other):
        """
        Five-valued XOR logic operation.
        
        Implements XOR operation for {0, 1, X, D, D'} value system following
        D-algebra rules. XOR with 1 inverts the D-values.
        
        Args:
            other: Another GateValue to XOR with
            
        Returns:
            Result of the XOR operation
        """
        a, b = self, other

        # Unknown propagates through XOR
        if a == NodeValue.UNKNOWN or b == NodeValue.UNKNOWN:
            return NodeValue.UNKNOWN

        # XOR truth table for all value combinations
        if a == NodeValue.ZERO:
            if b == NodeValue.ZERO:
                return NodeValue.ZERO
            if b == NodeValue.ONE:
                return NodeValue.ONE
            if b == NodeValue.D:
                return NodeValue.D
            if b == NodeValue.D_BAR:
                return NodeValue.D_BAR
        if a == NodeValue.ONE:
            if b == NodeValue.ZERO:
                return NodeValue.ONE
            if b == NodeValue.ONE:
                return NodeValue.ZERO
            if b == NodeValue.D:
                return NodeValue.D_BAR
            if b == NodeValue.D_BAR:
                return NodeValue.D
        if a == NodeValue.D:
            if b == NodeValue.ZERO:
                return NodeValue.D
            if b == NodeValue.ONE:
                return NodeValue.D_BAR
            if b == NodeValue.D:
                return NodeValue.ZERO
            if b == NodeValue.D_BAR:
                return NodeValue.ONE
        if a == NodeValue.D_BAR:
            if b == NodeValue.ZERO:
                return NodeValue.D_BAR
            if b == NodeValue.ONE:
                return NodeValue.D
            if b == NodeValue.D:
                return NodeValue.ONE
            if b == NodeValue.D_BAR:
                return NodeValue.ZERO
        return NodeValue.UNKNOWN

    def __invert__(self):
        """
        Five-valued NOT logic operation (inversion).
        
        Inverts the gate value: 0->1, 1->0, D->D', D'->D, X->X
        
        Returns:
            Inverted gate value
        """
        if self == NodeValue.ZERO:
            return NodeValue.ONE
        elif self == NodeValue.ONE:
            return NodeValue.ZERO
        elif self == NodeValue.D:
            return NodeValue.D_BAR
        elif self == NodeValue.D_BAR:
            return NodeValue.D
        else:
            return self

    def __eq__(self, other):
        """Check equality between two GateValue instances."""
        if isinstance(other, NodeValue):
            return self.value == other.value
        return False

class Wire:
    """
    Represents a wire connecting gates in a circuit.
    
    A wire has one input gate (source) and multiple output gates (destinations).
    The wire facilitates the connection between gates by tracking these relationships
    and establishing fan-in/fan-out connections.
    
    Attributes:
        wire_name: Unique identifier for this wire
        input_gate: The gate that drives this wire (produces its value)
        output_gates: List of gates that read from this wire
    """
    def __init__(self, wire_name: str):
        self.name = wire_name
        self.input_gate: Gate = None
        self.output_gates: list[Gate] = []

    def add_input_gate(self, gate: 'Gate'):
        """
        Set the input gate that drives this wire.
        
        Args:
            gate: The gate that produces the value for this wire
            
        Raises:
            AssertionError: If an input gate has already been assigned
        """
        assert self.input_gate is None, "Input gate already exists"
        self.input_gate = gate

    def add_output_gate(self, gate: 'Gate'):
        """
        Add a gate that reads from this wire.
        
        Args:
            gate: The gate that uses this wire as an input
        """
        self.output_gates.append(gate)

    def connect_gates(self):
        """
        Establish fan-in/fan-out relationships between connected gates.
        
        Creates bidirectional connections: each output gate gets this wire's
        input gate as a fan-in, and the input gate gets all output gates as fan-outs.
        """
        for gate in self.output_gates:
            gate.add_fan_in_gate(self.input_gate)
            self.input_gate.add_fan_out_gate(gate)
    
    def __str__(self):
        """String representation showing wire connections."""
        return f"Wire: {self.name}, Input gate: {self.input_gate.name}, Output gates: {[gate.name for gate in self.output_gates]}"

class Gate:
    """
    Base class for all logic gates in the circuit.
    
    A gate has inputs (fan-in), outputs (fan-out), and evaluates based on
    its gate type. It tracks input/output values, connections to other gates,
    and maintains evaluation state.
    
    Attributes:
        gate_name: Unique identifier for this gate
        gate_type: Type of gate (AND, OR, NOT, etc.)
        input_number: Number of input connections
        gate_input_values: Current values on input lines
        gate_output_value: Current output value
        fan_in_gates: List of gates providing input to this gate
        fan_out_gates: List of gates receiving output from this gate
        fan_in_wires: List of wires providing input to this gate
        fan_out_wire: Wire receiving output from this gate
        forward_count: Number of times this gate has been evaluated
    """
    def __init__(self, gate_type: GateType, gate_name: str, input_number: int):
        self.name = gate_name
        self.type = gate_type
        self.input_number = input_number
        self.input_values: list[NodeValue] = [NodeValue.UNKNOWN] * input_number
        self.output_value: NodeValue = NodeValue.UNKNOWN

        self.fan_in_gates: list['Gate'] = []
        self.fan_out_gates: list['Gate'] = []

        self.fan_in_wires: list[Wire] = []
        self.fan_out_wire: Wire = None

        self.forward_count = 0

    def forward(self):
        """
        Perform forward propagation: evaluate gate based on fan-in values.
        
        For non-INPUT gates, reads values from fan-in gates, evaluates the
        gate function, and updates the output value.
        
        Returns:
            The computed output value
        """
        if self.type != GateType.INPUT:
            input_values = [gate.output_value for gate in self.fan_in_gates]
            self.input_values = input_values
            self.output_value = self.evaluate(input_values)
        self.forward_count += 1
        return self.output_value

    def evaluate(self, input_values: list[NodeValue]):
        """
        Evaluate the gate's logic function (to be overridden by subclasses).
        
        Args:
            input_values: List of input gate values
            
        Returns:
            The computed output value
        """
        pass

    def set_input_value(self, values: list[NodeValue]):
        """
        Manually set the input values for this gate.
        
        Args:
            values: List of GateValue instances to assign to inputs
        """
        assert len(self.input_values) == self.input_number, "Number of input values does not match input number"
        self.input_values = values

    def set_output_value(self, value: NodeValue):
        """
        Manually set the output value for this gate.
        
        Args:
            value: GateValue to assign to the output
        """
        self.output_value = value

    def reset_values(self):
        """
        Reset the gate to its initial state.
        
        Clears input/output values and resets the forward count.
        """
        self.forward_count = 0
        self.input_values = [NodeValue.UNKNOWN] * self.input_number
        self.output_value = NodeValue.UNKNOWN

    def add_fan_in_gate(self, gate: 'Gate'):
        """
        Add a fan-in gate (a gate that provides input to this gate).
        
        Args:
            gate: The gate to add as a fan-in connection
        """
        assert len(self.fan_in_gates) < self.input_number, "Number of fan-in gates exceeds input number"
        self.fan_in_gates.append(gate)

    def add_fan_out_gate(self, gate: 'Gate'):
        """
        Add a fan-out gate (a gate that receives output from this gate).
        
        Args:
            gate: The gate to add as a fan-out connection
        """
        self.fan_out_gates.append(gate)

    def set_fan_in_gates(self, gates: list['Gate']):
        """
        Set all fan-in gates at once.
        
        Args:
            gates: List of gates that provide input to this gate
        """
        assert len(gates) == self.input_number, "Number of fan-in gates does not match input number"
        self.fan_in_gates = gates

    def set_fan_out_gates(self, gates: list['Gate']):
        """
        Set all fan-out gates at once.
        
        Args:
            gates: List of gates that receive output from this gate
        """
        self.fan_out_gates = gates

    def add_fan_in_wire(self, wire: Wire):
        """
        Add a fan-in wire (a wire that provides input to this gate).
        
        Args:
            wire: The wire to add as a fan-in connection
        """
        self.fan_in_wires.append(wire)

    def add_fan_out_wire(self, wire: Wire):
        """
        Add a fan-out wire (a wire that receives output from this gate).
        
        Args:
            wire: The wire to add as a fan-out connection
        """
        self.fan_out_wire = wire

    def set_fan_in_wires(self, wires: list[Wire]):
        """
        Set all fan-in wires at once.
        
        Args:
            wires: List of wires that provide input to this gate
        """
        self.fan_in_wires = wires

    def set_fan_out_wire(self, wire: Wire):
        """
        Set the fan-out wire at once.

        Args:
            wire: The wire to set as the fan-out connection
        """
        self.fan_out_wire = wire

    def is_evaluated(self):
        """
        Check if this gate has been evaluated at least once.
        
        Returns:
            True if forward() has been called, False otherwise
        """
        return self.forward_count > 0

    def is_unknown(self):
        """
        Check if this gate has an unknown output value.
        
        Returns:
            True if the output value is unknown, False otherwise
        """
        return self.output_value == NodeValue.UNKNOWN

    def is_in_D_frontier(self) -> bool:
        """
        Check if this gate is in the D frontier.
        
        Returns:
            True if the gate is in the D frontier, False otherwise
        """
        if self.output_value != NodeValue.UNKNOWN:
            return False
        for input_value in self.input_values:
            if input_value == NodeValue.D or input_value == NodeValue.D_BAR:
                return True
        return False

    def get_fan_in_gate_by_index(self, index: int) -> 'Gate':
        """
        Get the fan-in gate by index.
        
        Args:
            index: The index of the fan-in gate
        """
        return self.fan_in_gates[index]


    def get_controlling_value(self) -> NodeValue:
        """
        Get the controlling value of this gate.
        
        Returns:
            The controlling value of this gate
        """
        return NodeValue.UNKNOWN

    def get_non_controlling_value(self) -> NodeValue:
        """
        Get the non-controlling value of this gate.
        
        Returns:
            The non-controlling value of this gate
        """
        return NodeValue.UNKNOWN

    def is_inversion_gate(self) -> bool:
        """
        Check if this gate is an inversion gate.
        
        Returns:
            True if this gate is an inversion gate, False otherwise
        """
        return False

    def __str__(self):
        """String representation showing gate details and connections."""
        return f"Gate: {self.name}, Type: {self.type}, Input number: {self.input_number}, Input values: {self.input_values}, Output value: {self.output_value}, Forward count: {self.forward_count}, Fan-in gates: {[gate.name for gate in self.fan_in_gates]}, Fan-out gates: {[gate.name for gate in self.fan_out_gates]}"


class ORGate(Gate):
    """
    OR gate implementation.
    
    Outputs 1 if any input is 1, otherwise outputs based on five-valued logic.
    Requires at least 2 inputs.
    """
    def __init__(self, gate_name: str, input_number: int):
        super().__init__(GateType.OR, gate_name, input_number)
    
    def evaluate(self, input_values: list[NodeValue]):
        """Evaluate OR function across all inputs."""
        assert len(input_values) > 1, "OR gate takes at least two inputs"
        input_values = input_values
        output_value = input_values[0]
        for value in input_values[1:]:
            output_value = output_value | value
        return output_value

    def get_controlling_value(self) -> NodeValue:
        return NodeValue.ONE

    def get_non_controlling_value(self) -> NodeValue:
        return NodeValue.ZERO


class ANDGate(Gate):
    """
    AND gate implementation.
    
    Outputs 1 only if all inputs are 1, outputs 0 if any input is 0,
    otherwise outputs based on five-valued logic.
    Requires at least 2 inputs.
    """
    def __init__(self, gate_name: str, input_number: int):
        super().__init__(GateType.AND, gate_name, input_number)
    
    def evaluate(self, input_values: list[NodeValue]):
        """Evaluate AND function across all inputs."""
        assert len(input_values) > 1, "AND gate takes at least two inputs"
        output_value = input_values[0]
        for value in input_values[1:]:
            output_value = output_value & value
        return output_value

    def get_controlling_value(self) -> NodeValue:
        return NodeValue.ZERO

    def get_non_controlling_value(self) -> NodeValue:
        return NodeValue.ONE


class NOTGate(Gate):
    """
    NOT gate (inverter) implementation.
    
    Inverts the input: 0->1, 1->0, D->D', D'->D, X->X.
    Takes exactly 1 input.
    """
    def __init__(self, gate_name: str, input_number: int):
        super().__init__(GateType.NOT, gate_name, input_number)
    
    def evaluate(self, input_values: list[NodeValue]):
        """Evaluate NOT function (inversion)."""
        assert len(input_values) == 1, "NOT gate only takes one input"
        output_value = ~input_values[0]
        return output_value

    def is_inversion_gate(self) -> bool:
        return True


class BUFGate(Gate):
    """
    Buffer gate implementation.
    
    Passes through the input value unchanged. Used for signal propagation
    and timing purposes. Takes exactly 1 input.
    """
    def __init__(self, gate_name: str, input_number: int):
        super().__init__(GateType.BUF, gate_name, input_number)
    
    def evaluate(self, input_values: list[NodeValue]):
        """Evaluate BUF function (pass-through)."""
        assert len(input_values) == 1, "BUF gate only takes one input"
        output_value = input_values[0]
        return output_value


class NANDGate(Gate):
    """
    NAND gate implementation.
    
    Outputs the inverse of AND: 0 if all inputs are 1, 1 if any input is 0,
    otherwise outputs based on five-valued logic.
    Requires at least 2 inputs.
    """
    def __init__(self, gate_name: str, input_number: int):
        super().__init__(GateType.NAND, gate_name, input_number)
    
    def evaluate(self, input_values: list[NodeValue]):
        """Evaluate NAND function (inverted AND)."""
        assert len(input_values) > 1, "NAND gate takes at least two inputs"
        output_value = input_values[0]
        for value in input_values[1:]:
            output_value = output_value & value
        output_value = ~output_value
        return output_value

    def get_controlling_value(self) -> NodeValue:
        return NodeValue.ZERO

    def get_non_controlling_value(self) -> NodeValue:
        return NodeValue.ONE

    def is_inversion_gate(self) -> bool:
        return True


class NORGate(Gate):
    """
    NOR gate implementation.
    
    Outputs the inverse of OR: 0 if any input is 1, 1 if all inputs are 0,
    otherwise outputs based on five-valued logic.
    Requires at least 2 inputs.
    """
    def __init__(self, gate_name: str, input_number: int):
        super().__init__(GateType.NOR, gate_name, input_number)
    
    def evaluate(self, input_values: list[NodeValue]):
        """Evaluate NOR function (inverted OR)."""
        assert len(input_values) > 1, "NOR gate takes at least two inputs"
        output_value = input_values[0]
        for value in input_values[1:]:
            output_value = output_value | value
        output_value = ~output_value
        return output_value

    def get_controlling_value(self) -> NodeValue:
        return NodeValue.ONE

    def get_non_controlling_value(self) -> NodeValue:
        return NodeValue.ZERO

    def is_inversion_gate(self) -> bool:
        return True

class XORGate(Gate):
    """
    XOR (exclusive OR) gate implementation.
    
    Outputs 1 if an odd number of inputs are 1, 0 if an even number are 1.
    Supports five-valued logic with D-algebra.
    Requires at least 2 inputs.
    """
    def __init__(self, gate_name: str, input_number: int):
        super().__init__(GateType.XOR, gate_name, input_number)
    
    def evaluate(self, input_values: list[NodeValue]):
        """Evaluate XOR function across all inputs."""
        assert len(input_values) > 1, "XOR gate takes at least two inputs"
        output_value = input_values[0]
        for value in input_values[1:]:
            output_value = output_value ^ value
        return output_value
    
    def is_inversion_gate(self) -> bool:
        return True

class XNORGate(Gate):
    """
    XNOR (exclusive NOR) gate implementation.
    
    Outputs 1 if an even number of inputs are 1, 0 if an odd number are 1.
    Inverse of XOR. Supports five-valued logic with D-algebra.
    Requires at least 2 inputs.
    """
    def __init__(self, gate_name: str, input_number: int):
        super().__init__(GateType.XNOR, gate_name, input_number)
    
    def evaluate(self, input_values: list[NodeValue]):
        """Evaluate XNOR function (inverted XOR)."""
        assert len(input_values) > 1, "XNOR gate takes at least two inputs"
        output_value = input_values[0]
        for value in input_values[1:]:
            output_value = output_value ^ value
        output_value = ~output_value
        return output_value


class INPUTGate(Gate):
    """
    INPUT gate (primary input) implementation.
    
    Represents a primary input to the circuit. Has no fan-in gates;
    its value is set externally. Takes 0 inputs.
    """
    def __init__(self, gate_name: str, input_number: int = 0):
        super().__init__(GateType.INPUT, gate_name, input_number)

    def evaluate(self, input_values: list[NodeValue]):
        """
        Return the externally-set output value.
        
        INPUT gates don't compute; they simply provide their preset value.
        """
        return self.output_value


class OUTPUTGate(Gate):
    """
    OUTPUT gate (primary output) implementation.
    
    Represents a primary output of the circuit. Simply passes through
    the value from its single fan-in gate. Takes exactly 1 input.
    """
    def __init__(self, gate_name: str, input_number: int = 1):
        super().__init__(GateType.OUTPUT, gate_name, input_number)
    
    def evaluate(self, input_values: list[NodeValue]):
        """Pass through the input value to the output."""
        if len(input_values) == 1:
            return input_values[0]
        else:
            return NodeValue.UNKNOWN