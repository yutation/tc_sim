"""
Main entry point for circuit testing and fault simulation.

This module provides a command-line interface for running:
- DFS (Deductive Fault Simulation)
- PODEM (Path-Oriented Decision Making) test generation
- Cross-verification between PODEM and DFS results
"""

from tc_sim.podem import PODEMWrapper
from tc_sim.deductive_fault_simulator import DFSWrapper
from tc_sim.cross_verification import CrossVerification
import argparse


def main():
    """
    Main function that parses command-line arguments and executes the appropriate
    fault simulation or test generation algorithm.
    
    Command-line options:
    - --DFS: Run Deductive Fault Simulation
    - --PODEM: Run PODEM test pattern generation
    - --CROSS_VERIFY: Cross-verify PODEM and DFS results
    - -c/--circuit: Path to circuit netlist file
    - -f/--faults: Path to fault list file
    - -t/--tests: Path to test pattern file (for DFS)
    - -o/--output: Path to output file
    - -v/--verbose: Enable verbose output
    """
    # Set up argument parser with mutually exclusive operation modes
    parser = argparse.ArgumentParser(description="Run PODEM or DFS for a given circuit")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--DFS", action="store_true", 
                      help="Use DFS (Deductive Fault Simulation)")
    group.add_argument("--PODEM", action="store_true", 
                      help="Use PODEM (Path-Oriented Decision Making)")
    group.add_argument("--CROSS_VERIFY", action="store_true", 
                      help="Cross-verify the results of PODEM and DFS")
    
    # Add common arguments for all modes
    parser.add_argument("-c", "--circuit", type=str, 
                       help="Path to the circuit file")
    parser.add_argument("-f", "--faults", type=str, 
                       help="Path to the fault file")
    parser.add_argument("-t", "--tests", type=str, 
                       help="Path to the test pattern file")
    parser.add_argument("-o", "--output", type=str, 
                       help="Path to the output file")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Execute the selected operation mode
    if args.DFS:
        # Run Deductive Fault Simulation
        dfs_wrapper = DFSWrapper(args.circuit)
        dfs_wrapper.add_test_pattern_from_file(args.tests)
        dfs_wrapper.run_all_test_patterns()
        
        # Save results with or without verbose information
        if args.verbose:
            dfs_wrapper.save_detected_fault_set_list_verbose(args.output)
        else:
            dfs_wrapper.save_detected_fault_set_list(args.output)
            
    elif args.PODEM:
        # Run PODEM test pattern generation
        podem_wrapper = PODEMWrapper(args.circuit)
        podem_wrapper.add_faults_from_file(args.faults)
        podem_wrapper.run_all_faults()
        
        # Save test patterns with or without verbose information
        if args.verbose:
            podem_wrapper.save_test_patterns_verbose(args.output)
        else:
            podem_wrapper.save_test_patterns(args.output)
            
    elif args.CROSS_VERIFY:
        # Run cross-verification between PODEM and DFS
        cross_verification = CrossVerification(args.circuit, args.faults)
        failure_count = cross_verification.cross_verify()
        print(f"{failure_count} failures in PODEM and DFS cross-verification "
              f"for {args.circuit} and {args.faults}")


if __name__ == "__main__":
    main()
