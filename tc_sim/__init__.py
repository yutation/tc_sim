"""
TC_SIM - Test and Circuit Simulation Package

This package provides tools for digital circuit testing and fault simulation,
including implementations of:

- PODEM (Path-Oriented Decision Making): Automatic test pattern generation
- DFS (Deductive Fault Simulation): Efficient fault coverage analysis
- Five-valued logic system with D-algebra for fault simulation
- Circuit netlist parsing and evaluation
- Single Stuck-At (SSA) fault model

Main Components:
----------------
- circuit: Circuit representation, parsing, and evaluation
- gate: Gate types, logic operations, and five-valued logic
- fault: Fault models and utilities
- podem: PODEM test generation algorithm
- deductive_fault_simulator: Deductive fault simulation algorithm
- cross_verification: Verification between PODEM and DFS results
- utils: Utility functions for file operations

Usage Example:
--------------
    from tc_sim.podem import PODEMWrapper
    from tc_sim.deductive_fault_simulator import DFSWrapper
    
    # Generate test patterns with PODEM
    podem = PODEMWrapper("circuit.txt")
    podem.add_faults_from_file("faults.txt")
    patterns = podem.run_all_faults()
    
    # Verify with deductive fault simulation
    dfs = DFSWrapper("circuit.txt")
    dfs.add_test_pattern_from_file("patterns.txt")
    detected = dfs.run_all_test_patterns()
"""

__version__ = "1.0.0"
__author__ = "ECE6140 Project"

# Import main classes for easy access
from .circuit import Circuit, CircuitWrapper, build_circuit_from_ECE6140_netlist
from .gate import Gate, GateType, NodeValue, Wire
from .fault import SSAFault, read_fault_file, sort_ssa_faults_by_node_name
from .podem import PODEMWrapper, PODEMGeneration
from .deductive_fault_simulator import DeductiveFaultSimulator, DFSWrapper
from .cross_verification import CrossVerification

__all__ = [
    # Circuit components
    'Circuit',
    'CircuitWrapper',
    'build_circuit_from_ECE6140_netlist',
    
    # Gate components
    'Gate',
    'GateType',
    'NodeValue',
    'Wire',
    
    # Fault components
    'SSAFault',
    'read_fault_file',
    'sort_ssa_faults_by_node_name',
    
    # PODEM
    'PODEMWrapper',
    'PODEMGeneration',
    
    # Deductive Fault Simulation
    'DeductiveFaultSimulator',
    'DFSWrapper',
    
    # Cross-verification
    'CrossVerification',
]

