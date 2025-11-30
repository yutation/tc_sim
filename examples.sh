python main.py --DFS -c ./files/s27.txt  -t ./files/s27_tests.txt -o ./results/plain/s27_dfs.txt
python main.py --DFS -c ./files/s298f_2.txt  -t ./files/s298f_2_tests.txt -o ./results/plain/s298f_2_dfs.txt
python main.py --DFS -c ./files/s344f_2.txt  -t ./files/s344f_2_tests.txt -o ./results/plain/s344f_2_dfs.txt
python main.py --DFS -c ./files/s349f_2.txt  -t ./files/s349f_2_tests.txt -o ./results/plain/s349f_2_dfs.txt

python main.py --PODEM -c ./files/s27.txt -f ./files/s27_faults.txt -o ./results/plain/s27_podem.txt
python main.py --PODEM -c ./files/s298f_2.txt -f ./files/s298f_2_faults.txt -o ./results/plain/s298f_2_podem.txt
python main.py --PODEM -c ./files/s344f_2.txt -f ./files/s344f_2_faults.txt -o ./results/plain/s344f_2_podem.txt
python main.py --PODEM -c ./files/s349f_2.txt -f ./files/s349f_2_faults.txt -o ./results/plain/s349f_2_podem.txt

python main.py --DFS -c ./files/s27.txt  -t ./files/s27_tests.txt -o ./results/verbose/s27_dfs.txt -v
python main.py --DFS -c ./files/s298f_2.txt  -t ./files/s298f_2_tests.txt -o ./results/verbose/s298f_2_dfs.txt -v
python main.py --DFS -c ./files/s344f_2.txt  -t ./files/s344f_2_tests.txt -o ./results/verbose/s344f_2_dfs.txt -v
python main.py --DFS -c ./files/s349f_2.txt  -t ./files/s349f_2_tests.txt -o ./results/verbose/s349f_2_dfs.txt -v

python main.py --PODEM -c ./files/s27.txt -f ./files/s27_faults.txt -o ./results/verbose/s27_podem.txt -v
python main.py --PODEM -c ./files/s298f_2.txt -f ./files/s298f_2_faults.txt -o ./results/verbose/s298f_2_podem.txt -v
python main.py --PODEM -c ./files/s344f_2.txt -f ./files/s344f_2_faults.txt -o ./results/verbose/s344f_2_podem.txt -v
python main.py --PODEM -c ./files/s349f_2.txt -f ./files/s349f_2_faults.txt -o ./results/verbose/s349f_2_podem.txt -v

python main.py --CROSS_VERIFY -c ./files/s27.txt -f ./files/s27_faults.txt
python main.py --CROSS_VERIFY -c ./files/s298f_2.txt -f ./files/s298f_2_faults.txt
python main.py --CROSS_VERIFY -c ./files/s344f_2.txt -f ./files/s344f_2_faults.txt
python main.py --CROSS_VERIFY -c ./files/s349f_2.txt -f ./files/s349f_2_faults.txt


