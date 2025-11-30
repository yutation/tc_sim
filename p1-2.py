from tc_sim.deductive_fault_simulator import DFSWrapper

input_list = ["1110101", "10101010101010101","101010101010101011111111", "101010101010101011111111"]
file_name_list = ["s27","s298f_2", "s344f_2", "s349f_2"]

dfs_wrapper = DFSWrapper(f"./files/{file_name_list[0]}.txt")
dfs_wrapper.deductive_fault_evaluate_circuit_with_normal_input(input_list[0])

# dfs_wrapper.print_str_final_fault_list()