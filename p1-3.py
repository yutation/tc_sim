from tc_sim.podem import PODEMWrapper

podem_wrapper = PODEMWrapper(f"./files/s27.txt", f"./project3_data/s27_faults.txt")
podem_wrapper.run_all_faults()
podem_wrapper.save_test_patterns(f"./project3_data/s27_test_patterns.txt")

podem_wrapper = PODEMWrapper(f"./files/s298f_2.txt", f"./project3_data/s298f_2_faults.txt")
podem_wrapper.run_all_faults()
podem_wrapper.save_test_patterns(f"./project3_data/s298f_2_test_patterns.txt")

podem_wrapper = PODEMWrapper(f"./files/s344f_2.txt", f"./project3_data/s344f_2_faults.txt")
podem_wrapper.run_all_faults()
podem_wrapper.save_test_patterns(f"./project3_data/s344f_2_test_patterns.txt")

podem_wrapper = PODEMWrapper(f"./files/s349f_2.txt", f"./project3_data/s349f_2_faults.txt")
podem_wrapper.run_all_faults()
podem_wrapper.save_test_patterns(f"./project3_data/s349f_2_test_patterns.txt")