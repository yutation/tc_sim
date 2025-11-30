from tc_sim.cross_verification import CrossVerification

cross_verification = CrossVerification(f"./files/s27.txt", f"./project3_data/s27_faults.txt")
failure_count = cross_verification.cross_verify()
print(f"Total failure count: {failure_count}")

cross_verification = CrossVerification(f"./files/s298f_2.txt", f"./project3_data/s298f_2_faults.txt")
failure_count = cross_verification.cross_verify()
print(f"Total failure count: {failure_count}")

cross_verification = CrossVerification(f"./files/s344f_2.txt", f"./project3_data/s344f_2_faults.txt")
failure_count = cross_verification.cross_verify()
print(f"Total failure count: {failure_count}")

cross_verification = CrossVerification(f"./files/s349f_2.txt", f"./project3_data/s349f_2_faults.txt")
failure_count = cross_verification.cross_verify()
print(f"Total failure count: {failure_count}")