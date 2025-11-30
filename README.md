# ECE6140 Project: Digital Circuit Simulation & ATPG Tool

This project implements **Deductive Fault Simulation (DFS)** and **Path-Oriented Decision Making (PODEM)** algorithms for digital circuits. It allows for fault simulation given test vectors and automatic test pattern generation (ATPG) for specified faults.

## 1. Simulation Environment

This program is written in **Python 3**. It relies only on Python's standard libraries and does not require any external package installations (no `pip install` needed).

### Requirements
-   **Python 3.6+**
-   Standard libraries used: `argparse`, `os`, `sys`, `typing`, `collections`, `enum`, `copy`.

## 2. Setup Instructions

1.  **Clone or Download** the repository to your local machine.
2.  Ensure you have Python 3 installed.
    ```bash
    python --version
    ```
3.  Navigate to the project root directory:
    ```bash
    cd /path/to/project
    ```

## 3. How to Run the Program

The program is executed via the `main.py` script. It supports three main modes: **DFS**, **PODEM**, and **Cross Verification**.

### Mode 1: Deductive Fault Simulation (DFS)
Runs fault simulation on a circuit using provided test patterns.

**Usage:**
```bash
python main.py --DFS -c <circuit_file> -t <test_patterns_file> -o <output_file> [-v]
```

-   `-c, --circuit`: Path to the circuit netlist file.
-   `-t, --tests`: Path to the file containing test patterns (input vectors).
-   `-o, --output`: Path where the detected faults will be saved.
-   `-v, --verbose`: (Optional) detailed output format.

**Example:**
```bash
python main.py --DFS -c ./files/s27.txt -t ./files/s27_tests.txt -o ./results/plain/s27_dfs.txt
```

### Mode 2: PODEM (ATPG)
Generates test patterns for a list of specified faults.

**Usage:**
```bash
python main.py --PODEM -c <circuit_file> -f <fault_file> -o <output_file> [-v]
```

-   `-c, --circuit`: Path to the circuit netlist file.
-   `-f, --faults`: Path to the file containing faults to generate tests for.
-   `-o, --output`: Path where the generated test patterns will be saved.
-   `-v, --verbose`: (Optional) detailed output format.

**Example:**
```bash
python main.py --PODEM -c ./files/s27.txt -f ./files/s27_faults.txt -o ./results/plain/s27_podem.txt
```

### Mode 3: Cross Verification
Verifies the correctness of the ATPG by running PODEM to generate a pattern for a fault, and then running DFS with that pattern to confirm the fault is detected.

**Usage:**
```bash
python main.py --CROSS_VERIFY -c <circuit_file> -f <fault_file>
```

**Example:**
```bash
python main.py --CROSS_VERIFY -c ./files/s27.txt -f ./files/s27_faults.txt
```

## 4. Input File Formats

### Circuit Netlist (`.txt`)
Describes the circuit connections and gates.
-   **Gate format:** `GATE_TYPE INPUT_NODES... OUTPUT_NODE`
-   **I/O definition:** `INPUT NODE_LIST -1` / `OUTPUT NODE_LIST -1`
-   **Example (`s27.txt`):**
    ```text
    INV 9 5
    AND 12 13 7
    INPUT 1 2 3 4 -1
    OUTPUT 7 9 5 -1
    ```

### Fault File (`.txt`)
Specifies Stuck-At Faults (SAF).
-   **Format:** `NODE_ID stuck at VALUE`
-   **Example:**
    ```text
    16 stuck at 0
    10 stuck at 1
    ```

### Test Pattern File (`.txt`)
Contains binary strings representing input vectors. The order corresponds to the order of inputs defined in the netlist.
-   **Format:** One binary string per line.
-   **Example:**
    ```text
    1101101
    0101001
    ```

## 5. Output Files

### DFS Output
DFS generates **one result file per test vector** provided in the test patterns file. Each output file lists all faults detected by that specific test vector.

-   **Standard Format (non-verbose):**
    -   Each line contains one detected fault.
    -   Format: `NODE_ID stuck at VALUE`
    -   Example:
        ```text
        1 stuck at 1
        3 stuck at 1
        5 stuck at 0
        16 stuck at 1
        ```

-   **Verbose Format (`-v` flag):**
    -   Includes metadata header followed by the detected faults.
    -   Header contains: circuit filename, input test vector used, and total fault count.
    -   Example:
        ```text
        Circuit file: ./files/s27.txt
        Fault set file: None
        Input values: 1101101
        Detected faults: 13
        ------FAULTS DETECTED------
        1 stuck at 1
        3 stuck at 1
        5 stuck at 0
        ...
        ```

**File Naming:** If you have N test vectors, you'll get N output files (e.g., `output_0.txt`, `output_1.txt`, ..., `output_N-1.txt`).

### PODEM Output
PODEM generates **one result file** containing test vectors for all specified faults. Each fault from the input fault file maps to **one line** in the output file.

-   **Standard Format (non-verbose):**
    -   Each line contains one test vector (same order as faults in input file).
    -   Format: Binary string with `X` for don't-care bits.
    -   Example (for 8 faults):
        ```text
        00XX010
        X00XXX0
        1XXX1XX
        11X101X
        10X00X0
        1XXX1XX
        00XX010
        X10XXXX
        ```
    -   Line 1 is the test vector for fault 1, line 2 for fault 2, etc.

-   **Verbose Format (`-v` flag):**
    -   Each line shows the fault followed by its test vector.
    -   Format: `NODE_ID stuck at VALUE: TEST_VECTOR`
    -   Example:
        ```text
        16 stuck at 0: 00XX010
        10 stuck at 1: X00XXX0
        12 stuck at 0: 1XXX1XX
        18 stuck at 1: 11X101X
        ```

**Undetectable Faults:**
-   Some faults may be **undetectable** (redundant faults that cannot be observed at any primary output).
-   When PODEM cannot generate a test pattern for a fault, it marks it as undetectable.
-   Undetectable faults are represented as a string of underscores (`_`) matching the input length.
-   Example (standard format):
    ```text
    00XX010
    _______
    1XXX1XX
    ```
    Here, the second fault is undetectable.
-   Example (verbose format):
    ```text
    16 stuck at 0: 00XX010
    22 stuck at 1: _______
    12 stuck at 0: 1XXX1XX
    ```

**Note:** The order of test vectors in the output corresponds to the order of faults in the input fault file.

