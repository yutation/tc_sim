#!/usr/bin/env python

import cframe
import argparse
import os
import copy

def main():
    parser = argparse.ArgumentParser(description="Perform implication and checking for an ISCAS circuit.")
    parser.add_argument("circuit", help="ISCAS file describing circuit under test")
    parser.add_argument("commands", help="Command file describing the commands to be applied")
    parser.add_argument("outfile", help="Base name for output files generated")
    parser.add_argument("-u", help="Enable unique D-drive", default=False, action='store_true')

    args = parser.parse_args()

    # Load circuit
    circ = cframe.Circuit(args.circuit)

    # Print circuit stats
    circ.print_summary()

    # Fault list
    faults = []

    # Unique D-drive flag
    D_drive = args.u

    # Open results file
    with open(args.outfile+".result", "w+") as ofile:

        # Read commands from file and process them
        for count, command_tuple in enumerate(cframe.Command.read_commands(args.commands)):
            command = command_tuple[0]

            # Faults are added to the fault list (used by imply_and_check routine)
            # Fault command, comm_tuple = (Command, gatename, value)
            if command == cframe.Command.Fault:
                loc = command_tuple[1] # location (gatename)
                val = command_tuple[2] # value (Roth) (One or Zero)
                faults.append(cframe.Fault(val, loc))
        
            # Implications call the imply_and_check routine and abort on conflict
            # Imply command, comm_tuple = (Command, gatename, value)
            if command == cframe.Command.Imply:
                loc = command_tuple[1] # location (gatename)
                val = command_tuple[2] # value (Roth)
                valid = imply_and_check(circ, faults, loc, val, D_drive)
                if not valid:
                    # print("CONFLICT. Commands aborted on command #%d\n" % count, file = ofile)
                    print("CONFLICT. Commands aborted on command #%d\n" % count)
                    exit()

            # J Frontier command calls the 
            if command == cframe.Command.Jfront:
                report_j_front(circ, ofile)

            # D Frontier command 
            if command == cframe.Command.Dfront:
                report_d_front(circ, ofile)

            # X path command
            if command == cframe.Command.Xpath:
                x_path_check(circ, ofile)

            # Display command
            if command == cframe.Command.Display:
                circ.write_state(ofile)
def forward_xor(a: cframe.Roth, b: cframe.Roth) -> cframe.Roth:
    '''
    	0	1	D	D'
    0	0	1	D	D'
    1	1	0	D'	D
    D	D	D'	0	1
    D'	D'	D	1	0
    '''
    assert(a != cframe.Roth.X and b != cframe.Roth.X)

    # table = {cframe.Roth.Zero: 
    #             {cframe.Roth.Zero: cframe.Roth.Zero,
    #              cframe.Roth.One: cframe.Roth.One,
    #              cframe.Roth.D: cframe.Roth.D,
    #              cframe.Roth.D_b: cframe.Roth.D_b},
    #          cframe.Roth.One:  [cframe.Roth.One, cframe.Roth.Zero, cframe.Roth.D_b, cframe.Roth.D],
    #          cframe.Roth.D: [cframe.Roth.D, cframe.Roth.D_b, cframe.Roth.Zero, cframe.Roth.One],
    #          cframe.Roth.D_b:[, cframe.Roth.D, cframe.Roth.One, cframe.Roth.Zero]}

    if(a == cframe.Roth.Zero):
        return copy.deepcopy(b)
    elif(b == cframe.Roth.Zero):
        return copy.deepcopy(a)
    elif(a == cframe.Roth.One):
        return cframe.Roth.invert(b)
    elif(b == cframe.Roth.One):
       return cframe.Roth.invert(a)
    elif(a == b):
        return cframe.Roth.Zero
    else:
        return cframe.Roth.One

def switch_to_fault(gate: cframe.Gate, activated):
    if(activated):
        if(gate.value == cframe.Roth.Zero):
            gate.value = cframe.Roth.D_b
        elif(gate.value == cframe.Roth.One):
            gate.value = cframe.Roth.D
    else:
        return False

def switch_to_activation(gate: cframe.Gate):
    if(gate.value == cframe.Roth.D_b):
        gate.value = cframe.Roth.Zero
        return True
    elif(gate.value == cframe.Roth.D):
        gate.value = cframe.Roth.One
        return True
    else:
        return False

def search_faults(gate_name: str, faults):
    # print(f"search_faults: {gate_name}, {len(faults)}")
    for fault in faults:
        # print(f"search_faults: {fault.stem}")
        if(gate_name == fault.stem):
            # print(f"search_faults: True")
            return True, fault.value
    return False, None

def update_fault_value(gate, value1, value2):
    if(value1 == cframe.Roth.Zero and value2 == cframe.Roth.Zero):
        gate.value = cframe.Roth.Zero
    elif(value1 == cframe.Roth.Zero and value2 == cframe.Roth.One):
        gate.value = cframe.Roth.D_b
    elif(value1 == cframe.Roth.One and value2 == cframe.Roth.Zero):
        gate.value = cframe.Roth.D
    elif(value1 == cframe.Roth.One and value2 == cframe.Roth.One):
        gate.value = cframe.Roth.One
    else:
        assert False, "Error update fault"
        
def search_D(circuit: cframe.Circuit, D_frontiers: list):
    for gate_name in circuit.gatemap:
        gate = circuit.gatemap[gate_name]
        if(gate.value == cframe.Roth.X):
            have_D = False
            for fanin_gate_name in gate.fanin:
                fanin_gate = circuit.gatemap[fanin_gate_name]
                if(fanin_gate.value == cframe.Roth.D or fanin_gate.value == cframe.Roth.D_b):
                    have_D = True
                    break
            if(have_D):
                current_value = copy.deepcopy(gate.value)
                eval_value = copy.deepcopy(gate.evaluate(circuit))
                gate.value = current_value
                if(eval_value == cframe.Roth.X):
                   D_frontiers.append(gate_name)
                else:
                    assert False, "Error: imply miss"


def solve_D(circuit: cframe.Circuit, gate_name: str):
    simple_gate_list = ["BUFF", "NOT"]
    basic_gate_list = ["AND", "NAND", "OR", "NOR"]
    complex_gate_list = ["XOR", "XNOR"]
    undefine_gate_list = ["UNDEFINED, DFF"]

    update_list = list()
    gate = circuit.gatemap[gate_name]

    assert(gate.gatetype in basic_gate_list or gate.gatetype in complex_gate_list)
    gate = circuit.gatemap[gate_name]
    '''
    D_value = cframe.Roth.X
    for fanin_gate_name in gate.fanin:
        fanin_gate = circuit.gatemap[fanin_gate_name]
            if(fanin_gate.value == cframe.Roth.D or fanin_gate.value == cframe.Roth.D_b):
                D_value = fanin_gate.value
                break
    '''

    if(gate.gatetype in basic_gate_list):
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

        uc_input_value = cframe.Roth.invert(forward_control)
        for fanin_gate_name in gate.fanin:
            fanin_gate = circuit.gatemap[fanin_gate_name]
            if(fanin_gate.value == cframe.Roth.X):
                update_list.append({"gate": fanin_gate_name, "value": uc_input_value})
        return True, update_list
    
    if(gate.gatetype in complex_gate_list):
        for fanin_gate_name in gate.fanin:
            fanin_gate = circuit.gatemap[fanin_gate_name]
            if(fanin_gate.value == cframe.Roth.X):
                update_list.append({"gate": fanin_gate_name, "value": cframe.Roth.Zero})
        return True, update_list

    return True, update_list

    
def search_J(circuit: cframe.Circuit, J_frontiers: list):
    for gate_name in circuit.gatemap:
        gate = circuit.gatemap[gate_name]
        if(gate.value != cframe.Roth.X):
            current_value = copy.deepcopy(gate.value)
            eval_value = copy.deepcopy(gate.evaluate(circuit))
            gate.value = current_value
            if(eval_value == cframe.Roth.X):
                J_frontiers.append(gate_name)

def have_X_path(circuit: cframe.Circuit, gate_name: str):
    gate = circuit.gatemap[gate_name]
    if(gate.value == cframe.Roth.X):
        if(len(gate.fanout) == 0):
            return True
        for fanout_gate_name in gate.fanout:
            result = have_X_path(circuit, fanout_gate_name)
            if(result):
                return True
        return False
    else:
        return False




# For a certain gate, check whether there is a port can be implied 
def check_gate(circuit: cframe.Circuit, gate_name: str):
    update_list = list()
    gate = circuit.gatemap[gate_name]

    simple_gate_list = ["BUFF", "NOT"]
    basic_gate_list = ["AND", "NAND", "OR", "NOR"]
    complex_gate_list = ["XOR", "XNOR"]
    undefine_gate_list = ["UNDEFINED, DFF"]

    assert(gate.gatetype not in undefine_gate_list)
    if(gate.gatetype == "INPUT"):
        return True, update_list

    # Forward Check
    current_value = copy.deepcopy(gate.value)
    eval_value = copy.deepcopy(gate.evaluate(circuit))
    gate.value = current_value
    current_value = copy.deepcopy(gate.value)

    if(current_value == cframe.Roth.X and eval_value == cframe.Roth.X):
        return True, update_list
    elif(current_value == cframe.Roth.X and eval_value != cframe.Roth.X):
        update_list.append({"gate": gate_name, "value": eval_value})
        return True, update_list
    elif(current_value != cframe.Roth.X and eval_value != cframe.Roth.X):
        if(current_value == eval_value):
            return True, update_list
        else:
            return False, update_list
    else:
        pass

    # Backward Check
    # Simple Gate
    if(gate.gatetype in simple_gate_list):
        if(gate.gatetype == "BUFF"):
            update_list.append({"gate": gate.fanin[0], "value": current_value})
        elif(gate.gatetype == "NOT"):
            update_list.append({"gate": gate.fanin[0], "value": cframe.Roth.invert(current_value)})
        else:
            assert False, "Gate type error"
        return True, update_list
    
    # Basic Gate
    if(gate.gatetype in basic_gate_list):
        if(gate.gatetype == 'AND'):
            forward_control = cframe.Roth.Zero
            backward_control = cframe.Roth.One
            inverting = False
        elif(gate.gatetype == 'NAND'):
            forward_control = cframe.Roth.Zero
            backward_control = cframe.Roth.Zero
            inverting = True
        elif(gate.gatetype == 'OR'):
            forward_control = cframe.Roth.One
            backward_control = cframe.Roth.Zero
            inverting = False
        elif(gate.gatetype == 'NOR'):
            forward_control = cframe.Roth.One
            backward_control = cframe.Roth.One
            inverting = True
        else:
            assert False, "Gate type error"

        uc_input_values = [cframe.Roth.invert(forward_control), cframe.Roth.D, cframe.Roth.D_b]
        if(current_value == backward_control):
            for input_gate_name in gate.fanin:
                update_list.append({"gate": input_gate_name, "value": cframe.Roth.invert(forward_control)})
        elif(current_value == cframe.Roth.invert(backward_control)):
            x_input_num = 0
            uc_input_num = 0
            x_gate_name = ""
            for input_gate_name in gate.fanin:
                input_gate = circuit.gatemap[input_gate_name]
                if(input_gate.value == cframe.Roth.X):
                    x_input_num += 1
                    x_gate_name = input_gate_name
                elif(input_gate.value in uc_input_values):
                    uc_input_num += 1
            # if(x_input_num == 1 and uc_input_num == len(gate.fanin) - 1):
            if(x_input_num == 1):
                 update_list.append({"gate": x_gate_name, "value": forward_control})   
        return True, update_list

    #   Complex gate
    if(gate.gatetype in complex_gate_list):
        x_input_num = 0
        x_gate_name = ""
        accum_value = cframe.Roth.Zero
        for input_gate_name in gate.fanin:
            input_gate = circuit.gatemap[input_gate_name]
            if(input_gate.value == cframe.Roth.X):
                x_input_num += 1
                x_gate_name = input_gate_name
            else:
                accum_value = forward_xor(accum_value, input_gate.value)
        if(x_input_num == 1):
            if(gate.gatetype == "XOR"):
                x_value = forward_xor(accum_value, current_value)
            elif(gate.gatetype == "XNOR"):
                x_value = forward_xor(accum_value, cframe.Roth.invert(current_value))
            else:
                assert False, "Gate type error"
            if(x_value == cframe.Roth.Zero or x_value == cframe.Roth.One):
                update_list.append({"gate": x_gate_name, "value": x_value})
        return True, update_list

    print(f"Gatetypr: {gate.gatetype}")
    assert False, "Gate type error"



        
def forward_gate(circuit: cframe.Circuit, gate_name: str, faults) -> bool:
    # print(f"forward: {gate_name}")
    gate = circuit.gatemap[gate_name]
    is_fault, fault_value = search_faults(gate_name, faults)
    if(is_fault and gate.value != cframe.Roth.X):
        activated = switch_to_activation(gate)
        result, update_list = check_gate(circuit, gate_name)
        switch_to_fault(gate, activated)
    else:
        result, update_list = check_gate(circuit, gate_name)
        

    if(not result):
        # print("Error")
        return False


    if(len(update_list) == 0):
        return True

    # print(update_list)
    if(len(update_list) == 1 and update_list[0]['gate'] == gate_name):
        if(is_fault):
            update_fault_value(gate, update_list[0]['value'], fault_value)
        else:
            gate.value = update_list[0]['value']
        # print(f"fGate: {gate_name} to forward") 
        for fanout_gate_name in gate.fanout:
            result =  forward_gate(circuit, fanout_gate_name, faults)
            if(not result):
                return False
        return True
    else:
        # print(f"fGate: {gate_name} to backward") 
        for update_pair in update_list:
            result = backward_gate(circuit, update_pair['gate'], update_pair['value'], faults)
            if(not result):
                return False
        return True


def backward_gate(circuit: cframe.Circuit, gate_name: str, value: cframe.Roth, faults) -> bool:
    # print(f"backward: {gate_name} = {value}")
    assert(value != cframe.Roth.X)
    gate = circuit.gatemap[gate_name]
    is_fault, fault_value = search_faults(gate_name, faults)

    

    # Check
    if(gate.value == value):
        return True
    if(gate.value != cframe.Roth.X):
        return False
    


    if(is_fault):
        update_fault_value(gate, value, fault_value)
        activated = switch_to_activation(gate)
        result, update_list = check_gate(circuit, gate_name)
        switch_to_fault(gate, activated)
    else:
        gate.value = value
        result, update_list = check_gate(circuit, gate_name)


        
    if(not result):
        return False
    # print(update_list)

    # print(f"bGate: {gate_name} to Backward")
    # Backward
    for update_pair in update_list:
        result = backward_gate(circuit, update_pair['gate'], update_pair['value'], faults)
        if(not result):
            return False
    
    # print(f"bGate: {gate_name} to forward")
    # Forward
    for fanout_gate_name in gate.fanout:
        result = forward_gate(circuit, fanout_gate_name, faults)
        if(not result):
            return False
    return True

        
    



def imply_and_check(circuit, faults, location, value, D_drive):
    """Imply a value and check for consequences in a circuit.

    Args:
       circuit (Circuit): The circuit under consideration.
       faults (list): A list of active Fault objects in the circuit.
       location (str): The string name of the gate location of the implication.
       value (Roth): A Roth object representing the value implied.
       D_drive (bool): Flag indicating whether to use unique D-drive.

    Returns:
       bool: A boolean indicating whether the implication is valid.
    """
    result = True
    # print(f"imply_and_check: fault_len:{len(faults)}")
    result = backward_gate(circuit, location, value, faults)
    if(not result):
        return False

    if(D_drive):
        d_frontier = list()
        search_D(circuit, d_frontier)
        while(len(d_frontier) == 1 and result):
            result, update_list = solve_D(circuit, d_frontier[0])
            for update_pair in update_list:
                result = backward_gate(circuit, update_pair['gate'], update_pair['value'], faults)
                if(not result):
                    return False
            d_frontier = list()
            search_D(circuit, d_frontier)
    # True indicates valid implication; False indicates a conflict
    return result


def report_j_front(circuit, outfile):
    """Determine the gates on the J frontier and write out to output file.

    Args:
       circuit (Circuit): The circuit under consideration.
       outfile (file pointer): Open file pointer for writing.
    """
    print("J-frontier", file = outfile)
    j_frontier = list()
    search_J(circuit, j_frontier)
    for j in j_frontier:
        print(j, file = outfile)

    print("$\n", file = outfile)



def report_d_front(circuit, outfile):
    """Determine the gates on the D frontier and write out to output file.

    Args:
       circuit (Circuit): The circuit under consideration.
       outfile (file pointer): Open file pointer for writing.
    """

    print("D-frontier", file = outfile)
    d_frontier = list()
    search_D(circuit, d_frontier)
    for d in d_frontier:
        print(d, file = outfile)

    print("$\n", file = outfile)


def x_path_check(circuit, outfile):
    """Determine for each gate on the D frontier if an X-path exists and write to output
    file.

    Args:
       circuit (Circuit): The circuit under consideration.
       outfile (file pointer): Open file pointer for writing.
    """
    print("X-PATH", file = outfile)
    d_frontier = list()
    search_D(circuit, d_frontier)
    for d in d_frontier:
        if(have_X_path(circuit, d)):
            print(d, file = outfile)
    print("$\n", file = outfile)
    


if __name__ == '__main__':

    # Open logging file
    logfile = os.path.join(os.path.dirname(__file__), "logs/imply.log")
    cframe.logging.basicConfig(filename=logfile,
                               format='%(asctime)s %(message)s',
                               datefmt='%m/%d/%Y %I:%M:%S %p',
                               level=cframe.logging.DEBUG)

    main()
