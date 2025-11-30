from tc_sim.podem import PODEMWrapper
from tc_sim.deductive_fault_simulator import DFSWrapper
from tc_sim.cross_verification import CrossVerification
import argparse


def main():
    parser = argparse.ArgumentParser(description="Run PODEM or DFS for a given circuit")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--DFS", action="store_true", help="Use DFS (Deductive Fault Simulation)")
    group.add_argument("--PODEM", action="store_true", help="Use PODEM (Path-Oriented Decision Making)")
    group.add_argument("--CROSS_VERIFY", action="store_true", help="Cross-verify the results of PODEM and DFS")
    parser.add_argument("-c","--circuit", type=str, help="Path to the circuit file")
    parser.add_argument("-f","--faults", type=str, help="Path to the fault file")
    parser.add_argument("-t","--tests", type=str, help="Path to the test pattern file")
    parser.add_argument("-o","--output", type=str, help="Path to the output file")
    args = parser.parse_args()
    if args.DFS:
        dfs_wrapper = DFSWrapper(args.circuit)
        dfs_wrapper.add_test_pattern_from_file(args.tests)
        dfs_wrapper.run_all_test_patterns()
        dfs_wrapper.save_detected_fault_set_list(args.output)
    elif args.PODEM:
        podem_wrapper = PODEMWrapper(args.circuit)
        podem_wrapper.add_faults_from_file(args.faults)
        podem_wrapper.run_all_faults()
        podem_wrapper.save_test_patterns(args.output)
    elif args.CROSS_VERIFY:
        cross_verification = CrossVerification(args.circuit, args.faults)
        failure_count = cross_verification.cross_verify()
        print(f"Total failure count: {failure_count}")
        
if __name__ == "__main__":
    main()
