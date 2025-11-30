#!/usr/bin/env python

import cframe
import argparse
import os
import copy



def main():
    parser = argparse.ArgumentParser(
        description="Perform deductive fault simulation for an ISCAS circuit and test set."
    )
    parser.add_argument("circuit", help="ISCAS file describing circuit under test")
    parser.add_argument("tests", help="File describing the tests to be applied")
    parser.add_argument("outfile", help="Base name for output files generated")
    parser.add_argument("-b", help="Simulate bridge faults in file provided")

    args = parser.parse_args()

    # Load circuit
    circ = cframe.Circuit(args.circuit)

    # Print circuit stats
    circ.print_summary()

    # Read in test set
    tests = cframe.read_testset(args.tests)

    # Print testset stats
    print("Testset has %d patterns" % (len(tests)))

    # If doing bridge simulation, read in bridges and do bridge fault simulation
    if args.b:
        bfaults = cframe.BridgeFault.read_bridges(args.b)
        print("Bridge faults read from file: %d" % (len(bfaults)))
        bridge_fault_sim(circ, tests, bfaults, args.outfile + ".result")

    # Else do normal ssl fault simulation
    else:
        ssl_fault_sim(circ, tests, args.outfile + ".result")

class Deductive_info:
    def __init__(self):
        self.fault_set = set()
        self.valid = False

class SSL_evaluator:
    def __init__(self, circuit: cframe.Circuit):
        self.circuit = circuit
        self.all_fault_set = self.get_all_faults() # str
        self.ud_fault_set = copy.deepcopy(self.all_fault_set) # str
        self.current_fault_set = set()
        self.gate_info_dict = dict()
        self.event_queue = list()

        self.simple_gate_list = ["BUFF", "NOT"]
        self.basic_gate_list = ["AND", "NAND", "OR", "NOR"]
        self.complex_gate_list = ["XOR", "XNOR"]
        self.undefine_gate_list = ["UNDEFINED, DFF"]
        self.eval_value_list = [cframe.Roth.Zero, cframe.Roth.One, cframe.Roth.X]
        
    def reset(self, test):
        self.gate_info_dict = dict()
        self.init_gate_info_dict()
        self.event_queue = list()
        self.set_and_eval(test)

    def complete_test(self):
        # for gate_name in self.gate_info_dict:
        #     if "108/1" in self.gate_info_dict[gate_name].fault_set:
        #         print(gate_name)

        result_set = set()
        for output_name in self.circuit.outputs:
            result_set = result_set | self.gate_info_dict[output_name].fault_set
            # print(f"{output_name}: {self.gate_info_dict[output_name].fault_set}")
        self.ud_fault_set = self.ud_fault_set - result_set
        self.current_fault_set = result_set
        # self.circuit.print_state() # DEBUG
        # self.print_all_set() # DEBUG
        return result_set

        
    def print_all_set(self):
        for key in self.gate_info_dict:
            print(f"{key}: {self.gate_info_dict[key].fault_set}, {self.circuit.gatemap[key].value}")


    def init_gate_info_dict(self):
        for gate_name in self.circuit.gatemap:
            self.gate_info_dict[gate_name] = Deductive_info()
    
    def set_and_eval(self, test):
        self.circuit.reset_flags()
        self.circuit.reset_values()
        self.circuit.set_inputs(test)
        self.circuit.evaluate()


    def get_all_faults(self):
        str_fault_set = set()
        for gate_name in self.circuit.gatemap:
            SA0 = gate_name + "/0"
            SA1 = gate_name + "/1"
            str_fault_set.add(SA0)
            str_fault_set.add(SA1)
        return str_fault_set

    def gate_deductive_eval(self, gate_name: str):
        gate = self.circuit.gatemap[gate_name]

        if(gate.gatetype == "INPUT"):
            if(gate.value != cframe.Roth.X):
                output_fault = self.fault_str(gate_name, cframe.Roth.invert(gate.value))
                output_fault_set = {output_fault}
            else:
                output_fault_set = set()
            self.gate_info_dict[gate_name].valid = True
            self.gate_info_dict[gate_name].fault_set = output_fault_set
            #print(output_fault_set)
            self.event_queue.extend(gate.fanout)
            return

        if(gate.gatetype in self.simple_gate_list):
            if(self.gate_info_dict[gate.fanin[0]].valid and gate.value in self.eval_value_list):
                if(gate.value == cframe.Roth.X):
                    output_fault_set = self.gate_info_dict[gate.fanin[0]].fault_set
                    # output_fault_set = set()
                else:
                    output_fault = self.fault_str(gate_name, cframe.Roth.invert(gate.value))
                    output_fault_set = self.gate_info_dict[gate.fanin[0]].fault_set | {output_fault}

                self.gate_info_dict[gate_name].valid = True
                self.gate_info_dict[gate_name].fault_set = output_fault_set
                #print(output_fault_set)
                self.event_queue.extend(gate.fanout)

            return

        if(gate.gatetype in self.basic_gate_list):
            if(gate.gatetype == 'AND'):
                forward_control = cframe.Roth.Zero
            elif(gate.gatetype == 'NAND'):
                forward_control = cframe.Roth.Zero
            elif(gate.gatetype == 'OR'):
                forward_control = cframe.Roth.One
            elif(gate.gatetype == 'NOR'):
                forward_control = cframe.Roth.One
            else:
                assert False, "Gate type error"
            
            have_control = False
            # have_X = False
            x_count = 0
            uc_set = set()
            c_set = copy.deepcopy(self.all_fault_set)
            x_set = set()
            for fanin_name in gate.fanin:
                fanin_gate = self.circuit.gatemap[fanin_name]
                if not self.gate_info_dict[fanin_name].valid:
                    return
                elif(fanin_gate.value == cframe.Roth.X):
                    # have_X = True
                    x_count += 1
                    x_set = self.gate_info_dict[fanin_name].fault_set
                elif(fanin_gate.value == forward_control):
                    have_control = True
                    c_set = c_set & self.gate_info_dict[fanin_name].fault_set
                elif(fanin_gate.value != forward_control):
                    uc_set = uc_set | self.gate_info_dict[fanin_name].fault_set
                else:
                    assert False

            if(x_count == 0):
                output_fault = self.fault_str(gate_name, cframe.Roth.invert(gate.value))
                if(have_control):
                    output_fault_set =(c_set - uc_set) | {output_fault}
                else:
                    output_fault_set =uc_set | {output_fault}
            else:
                if(have_control):
                    output_fault = self.fault_str(gate_name, cframe.Roth.invert(gate.value))
                    output_fault_set = {output_fault}
                elif(x_count == 1):
                    # output_fault_set = x_set
                    output_fault_set = set()
                else:
                    output_fault_set = set()
            
            # if(have_control):
            #     output_fault = self.fault_str(gate_name, cframe.Roth.invert(gate.value))
            #     if(not have_X):
            #         output_fault_set =(c_set - uc_set) | {output_fault}
            #     else:
            #         output_fault_set = {output_fault}
            # elif(not have_X):
            #     output_fault = self.fault_str(gate_name, cframe.Roth.invert(gate.value))
            #     output_fault_set =uc_set | {output_fault}
            # else:
            #     output_fault_set = set()

            self.gate_info_dict[gate_name].valid = True
            self.gate_info_dict[gate_name].fault_set = output_fault_set
            self.event_queue.extend(gate.fanout)
            return

        if(gate.gatetype in self.complex_gate_list):
            have_X = False
            c_set = set()
            for fanin_name in gate.fanin:
                fanin_gate = self.circuit.gatemap[fanin_name]
                if not self.gate_info_dict[fanin_name].valid:
                    return
                elif(fanin_gate.value == cframe.Roth.X):
                    have_X = True
                    c_set = c_set.symmetric_difference(self.gate_info_dict[fanin_name].fault_set)
                else:
                    c_set = c_set.symmetric_difference(self.gate_info_dict[fanin_name].fault_set)
            
            if(not have_X):
                output_fault = self.fault_str(gate_name, cframe.Roth.invert(gate.value))
                output_fault_set =c_set | {output_fault}
            else:
                output_fault_set = set()
                # output_fault_set =c_set

            self.gate_info_dict[gate_name].valid = True
            self.gate_info_dict[gate_name].fault_set = output_fault_set
            #print(output_fault_set)
            self.event_queue.extend(gate.fanout)
            return

    def deductive_eval(self):
        self.event_queue.extend(self.circuit.inputs)
        while(len(self.event_queue) != 0):
            current_name = self.event_queue.pop()
            if(current_name in self.event_queue):
                continue
            else:
                self.gate_deductive_eval(current_name)

    def bridge_eval(self, bfault: cframe.BridgeFault):
        gate_name_a = bfault.sites[0]
        gate_name_b = bfault.sites[1]
        gate_a = self.circuit.gatemap[gate_name_a]
        gate_b = self.circuit.gatemap[gate_name_b]

        
        if(bfault.bridgetype == "AND"):
            control_value = cframe.Roth.Zero
        elif(bfault.bridgetype == "OR"):
            control_value = cframe.Roth.One
        else:
            control_value = cframe.Roth.X
            assert False
        
        gate_a_fault = self.fault_str(gate_name_a, control_value)
        gate_b_fault = self.fault_str(gate_name_b, control_value)

        if((gate_a_fault in self.current_fault_set and gate_b.value == control_value) or
           (gate_b_fault in self.current_fault_set and gate_a.value == control_value)):
            return True
        else:
            return False
    

    def fault_str(self, gate_name: str, value: cframe.Roth) -> str:
        if(value == cframe.Roth.Zero):
            return gate_name + "/0"
        
        if(value == cframe.Roth.One):
            return gate_name + "/1"
        
        return gate_name + "/?"




def ssl_fault_sim(
    circuit: cframe.Circuit, tests: list[tuple[cframe.Roth, ...]], ssl_outfile: str
) -> None:
    """Perform deductive fault simulation given a Circuit and testset.

    Args:
       circuit (cframe.Circuit): The circuit under consideration.
       tests (list[tuple[Roth, ...]]): A list of tests to apply to the circuit.
       ssl_outfile (str): The name for the output file for SSL faults.

    """
    f = open(ssl_outfile, "w")
    print("# Test index: line/sa line/sa ...", file = f)
    print("# Detected", file = f)

    evaluator = SSL_evaluator(circuit)
    test_index = 0
    for test in tests:
        evaluator.reset(test)
        evaluator.deductive_eval()
        result_set = evaluator.complete_test()
        print(f"{test_index}:", file = f, end = "  ")
        count = 0
        for fault in result_set:
            count += 1
            if(count == len(result_set)):
                print(f"{fault}", file = f, end = "")
            else:
                print(f"{fault}", file = f, end = " ")
        print(file = f)
        test_index += 1
    print("$",file = f)

    print(file = f)
    print("# Undetected", file = f)
    for u_fault in evaluator.ud_fault_set:
        print(f"{u_fault}", file = f)
    # print("$",file = f)

    f.close()
    # print("TODO: Complete this function to perform deductive fault simulation for SSL faults.")


def bridge_fault_sim(
    circuit: cframe.Circuit,
    tests: list[tuple[cframe.Roth, ...]],
    bfaults: list[cframe.BridgeFault],
    outfile: str,
) -> None:
    """Perform deductive fault simulation given a Circuit, testset, and bridge faults.

    Args:
       circuit (cframe.Circuit): The circuit under consideration.
       tests (list[tuple[cframe.Roth, ...]]): A list of tests to apply to the circuit.
       bfaults (list[cframe.BridgeFault]): A list of BridgeFaults to simulate.
       outfile (str): The name for the output file.
    """

    evaluator = SSL_evaluator(circuit)
    test_index = 0
    for test in tests:
        evaluator.reset(test)
        evaluator.deductive_eval()
        evaluator.complete_test()
        for bfault in bfaults:
            if(bfault.flag):
                continue
            elif(evaluator.bridge_eval(bfault)):
                # print(bfault.sites, end = ", ")
                # print(bfault.bridgetype)
                bfault.flag = True
    
    f = open(outfile, "w")
    print("# Detected bridges", file = f)
    for i in range(len(bfaults)):
        if bfaults[i].flag:
            print(f"{i}", file = f)
    print(f"$", file=f)
    print(file=f)
    print("# Undetected bridges", file = f)
    for i in range(len(bfaults)):
        if not bfaults[i].flag:
            print(f"{i}", file = f)



    # print("TODO: Complete this function to perform deductive fault simulation for bridge faults.")


if __name__ == "__main__":
    # Open logging file
    logfile = os.path.join(os.path.dirname(__file__), "logs/dfsim.log")
    cframe.logging.basicConfig(
        filename=logfile,
        format="%(asctime)s %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=cframe.logging.DEBUG,
    )

    main()
