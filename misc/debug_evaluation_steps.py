#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tc_sim'))

from circuit import CircuitWrapper
from gate import GateValue

def debug_evaluation_steps():
    """Print detailed evaluation steps"""
    
    circuit_file = "./files/s27.txt"
    wrapper = CircuitWrapper(circuit_file)
    wrapper.build_circuit()
    
    circuit = wrapper.circuit
    
    # Open file for writing
    with open("evaluation_steps.txt", "w") as f:
        f.write("=" * 80 + "\n")
        f.write("DETAILED EVALUATION STEPS\n")
        f.write("=" * 80 + "\n")
        
        # Set input values
        f.write("\n1. SETTING INPUT VALUES:\n")
        input_gates = [circuit.gates[name] for name in circuit.input_port_names]
        for i, gate in enumerate(input_gates):
            gate.set_output_value(GateValue.ZERO)
            f.write(f"   {circuit.input_port_names[i]} = {gate.gate_output_value}\n")
        
        # Show initial state (excluding OUTPUT gates)
        f.write(f"\n2. INITIAL GATE STATES:\n")
        key_gates = ['buf_12', 'inv_18', 'nor_15', 'nor_11', 'or_17', 'nor_9', 'buf_19', 'and_7', 'and_20', 'inv_5', 'inv_13', 'nand_14', 'or_16']
        for gate_name in key_gates:
            if gate_name in circuit.gates:
                gate = circuit.gates[gate_name]
                fan_in_names = [g.gate_name for g in gate.fan_in_gates]
                f.write(f"   {gate_name}: {gate.gate_output_value} (fan-in: {fan_in_names})\n")
        
        # Show evaluation queue
        from collections import deque
        evaluation_queue = deque()
        for input_port_name in circuit.input_port_names:
            evaluation_queue.extend(circuit.gates[input_port_name].fan_out_gates)
        
        f.write(f"\n3. INITIAL EVALUATION QUEUE:\n")
        f.write(f"   {[g.gate_name for g in evaluation_queue]}\n")
        
        # Run evaluation step by step
        f.write(f"\n4. EVALUATION STEPS:\n")
        step = 0
        while len(evaluation_queue) > 0:  # Limit to 20 steps
            gate = evaluation_queue.popleft()
            f.write(f"\n   Step {step}: Evaluating {gate.gate_name}\n")
            f.write(f"   └─ Previous value: {gate.gate_output_value}\n")
            
            # Show fan-in values
            fan_in_values = [g.gate_output_value for g in gate.fan_in_gates]
            fan_in_names = [g.gate_name for g in gate.fan_in_gates]
            f.write(f"   └─ Fan-in values: {dict(zip(fan_in_names, fan_in_values))}\n")
            
            prev_output_value = gate.gate_output_value
            new_output_value = gate.forward()
            
            f.write(f"   └─ New value: {new_output_value}\n")
            f.write(f"   └─ Value changed: {prev_output_value != new_output_value}\n")
            
            if prev_output_value != new_output_value:
                fan_out_names = [g.gate_name for g in gate.fan_out_gates]
                f.write(f"   └─ Adding fan-out gates: {fan_out_names}\n")
                for fan_out_gate in gate.fan_out_gates:
                    evaluation_queue.append(fan_out_gate)
            else:
                f.write(f"   └─ No change, not adding fan-out gates\n")
            
            f.write(f"   └─ Queue now: {[g.gate_name for g in evaluation_queue]}\n")
            step += 1
        
        # Show final state
        f.write(f"\n5. FINAL GATE STATES:\n")
        for gate_name in key_gates:
            if gate_name in circuit.gates:
                gate = circuit.gates[gate_name]
                fan_in_names = [g.gate_name for g in gate.fan_in_gates]
                f.write(f"   {gate_name}: {gate.gate_output_value} (fan-in: {fan_in_names})\n")
        
        # Show OUTPUT gates
        f.write(f"\n6. OUTPUT GATES:\n")
        for output_name in circuit.output_port_names:
            output_gate = circuit.gates[output_name]
            fan_in_names = [g.gate_name for g in output_gate.fan_in_gates]
            fan_in_values = [g.gate_output_value for g in output_gate.fan_in_gates]
            f.write(f"   {output_name}: {output_gate.gate_output_value} (fan-in: {dict(zip(fan_in_names, fan_in_values))})\n")
        
        f.write(f"\n" + "=" * 80 + "\n")
    
    print("Evaluation steps saved to 'evaluation_steps.txt'")

if __name__ == "__main__":
    debug_evaluation_steps()

