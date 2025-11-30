#!/usr/bin/env python3
"""
Random Test Vector Analysis for Fault Coverage

This script applies random test vectors to digital circuits and analyzes
fault coverage progression. It generates plots showing test number vs
coverage ratio and calculates the number of vectors needed for 75% and 90% coverage.

Author: ECE6140 Project
Date: 2024
"""

import os
import sys
import random
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Set
import time
from collections import defaultdict

# Add the tc_sim directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tc_sim.deductive_fault_simulator import DFSWrapper
from tc_sim.circuit import build_circuit_from_ECE6140_netlist
from tc_sim.gate import NodeValue


class RandomTestAnalyzer:
    """
    Analyzes fault coverage using random test vectors.
    
    This class generates random test vectors, applies them to circuits,
    tracks fault coverage progression, and generates analysis plots.
    """
    
    def __init__(self, circuit_files: List[str], max_tests: int = 1000, random_seed: int = 42):
        """
        Initialize the analyzer with circuit files.
        
        Args:
            circuit_files: List of paths to circuit netlist files
            max_tests: Maximum number of random test vectors to apply
            random_seed: Fixed seed for reproducible random test generation
        """
        self.circuit_files = circuit_files
        self.max_tests = max_tests
        self.results = {}
        self.random_seed = random_seed
        # Set fixed seed for reproducible results
        random.seed(random_seed)
        np.random.seed(random_seed)
        
    def generate_random_test_vector(self, num_inputs: int) -> str:
        """
        Generate a random test vector as a binary string.
        
        Args:
            num_inputs: Number of primary inputs in the circuit
            
        Returns:
            Binary string representing the test vector
        """
        return ''.join(random.choice(['0', '1']) for _ in range(num_inputs))
    
    def analyze_circuit(self, circuit_file: str) -> Dict:
        """
        Analyze a single circuit with random test vectors.
        
        Args:
            circuit_file: Path to the circuit netlist file
            
        Returns:
            Dictionary containing analysis results
        """
        print(f"Analyzing circuit: {circuit_file}")
        
        # Initialize the fault simulator
        dfs_wrapper = DFSWrapper(circuit_file)
        
        # Get circuit information
        num_inputs = len(dfs_wrapper.circuit.input_port_names)
        print(f"  Number of inputs: {num_inputs}")
        
        # Get total number of possible faults
        # First apply a dummy test to initialize the fault simulator
        dummy_test = '0' * num_inputs
        dfs_wrapper.deductive_fault_evaluate_circuit_with_normal_input(dummy_test)
        all_faults = dfs_wrapper.deductive_fault_simulator.get_all_faults()
        total_faults = len(all_faults)
        print(f"  Total possible faults: {total_faults}")
        
        # Track coverage progression
        detected_faults = set()
        coverage_history = []
        test_vectors = []
        
        # Apply random test vectors
        for test_num in range(1, self.max_tests + 1):
            # Generate random test vector
            test_vector = self.generate_random_test_vector(num_inputs)
            test_vectors.append(test_vector)
            
            # Apply test vector and get detected faults
            try:
                detected_faults_current = set(dfs_wrapper.deductive_fault_evaluate_circuit_with_normal_input(test_vector))
                detected_faults.update(detected_faults_current)
                
                # Calculate coverage percentage
                coverage_percentage = (len(detected_faults) / total_faults) * 100
                coverage_history.append(coverage_percentage)
                
                # Print progress every 100 tests
                if test_num % 100 == 0:
                    print(f"    Test {test_num}: Coverage = {coverage_percentage:.2f}% ({len(detected_faults)}/{total_faults})")
                
            except Exception as e:
                print(f"    Error applying test vector {test_num}: {e}")
                coverage_history.append(coverage_history[-1] if coverage_history else 0)
        
        # Find thresholds
        test_75 = self._find_threshold_test(coverage_history, 75.0)
        test_90 = self._find_threshold_test(coverage_history, 90.0)
        
        return {
            'circuit_file': circuit_file,
            'num_inputs': num_inputs,
            'total_faults': total_faults,
            'final_coverage': coverage_history[-1] if coverage_history else 0,
            'final_detected_faults': len(detected_faults),
            'test_75_percent': test_75,
            'test_90_percent': test_90,
            'coverage_history': coverage_history,
            'test_vectors': test_vectors,
            'detected_faults': detected_faults
        }
    
    def _find_threshold_test(self, coverage_history: List[float], threshold: float) -> int:
        """
        Find the test number where coverage first reaches the threshold.
        
        Args:
            coverage_history: List of coverage percentages
            threshold: Coverage threshold to find
            
        Returns:
            Test number where threshold is first reached, or -1 if never reached
        """
        for i, coverage in enumerate(coverage_history):
            if coverage >= threshold:
                return i + 1  # Test numbers are 1-indexed
        return -1
    
    def analyze_all_circuits(self) -> Dict:
        """
        Analyze all circuits and return comprehensive results.
        
        Returns:
            Dictionary containing results for all circuits
        """
        print("Starting random test vector analysis...")
        print(f"Maximum tests per circuit: {self.max_tests}")
        print("=" * 60)
        
        all_results = {}
        
        for circuit_file in self.circuit_files:
            try:
                result = self.analyze_circuit(circuit_file)
                all_results[os.path.basename(circuit_file)] = result
                print(f"Completed analysis for {os.path.basename(circuit_file)}")
                print("-" * 40)
            except Exception as e:
                print(f"Error analyzing {circuit_file}: {e}")
                continue
        
        self.results = all_results
        return all_results
    
    def create_coverage_plots(self, save_dir: str = None):
        """
        Create plots showing test number vs coverage ratio for all circuits.
        
        Args:
            save_dir: Directory to save plots (if None, displays them)
        """
        if not self.results:
            print("No results available. Run analyze_all_circuits() first.")
            return
        
        # Create individual plots for each circuit
        for circuit_name, result in self.results.items():
            plt.figure(figsize=(12, 8))
            
            test_numbers = range(1, len(result['coverage_history']) + 1)
            coverage_history = result['coverage_history']
            
            plt.plot(test_numbers, coverage_history, 'b-', linewidth=2, label='Coverage %')
            plt.axhline(y=75, color='r', linestyle='--', alpha=0.7, label='75% Threshold')
            plt.axhline(y=90, color='g', linestyle='--', alpha=0.7, label='90% Threshold')
            
            # Mark threshold points
            if result['test_75_percent'] > 0:
                plt.axvline(x=result['test_75_percent'], color='r', linestyle=':', alpha=0.7)
                plt.plot(result['test_75_percent'], 75, 'ro', markersize=8, label=f'75% at test {result["test_75_percent"]}')
            
            if result['test_90_percent'] > 0:
                plt.axvline(x=result['test_90_percent'], color='g', linestyle=':', alpha=0.7)
                plt.plot(result['test_90_percent'], 90, 'go', markersize=8, label=f'90% at test {result["test_90_percent"]}')
            
            plt.xlabel('Test Number')
            plt.ylabel('Fault Coverage (%)')
            plt.title(f'Fault Coverage vs Test Number\\n{circuit_name}')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.ylim(0, 100)
            
            if save_dir:
                plot_path = os.path.join(save_dir, f'{circuit_name}_coverage_plot.png')
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                print(f"Plot saved: {plot_path}")
            else:
                plt.show()
            
            plt.close()
        
        # Create combined plot
        plt.figure(figsize=(14, 10))
        colors = ['blue', 'red', 'green', 'orange', 'purple']
        
        for i, (circuit_name, result) in enumerate(self.results.items()):
            test_numbers = range(1, len(result['coverage_history']) + 1)
            coverage_history = result['coverage_history']
            color = colors[i % len(colors)]
            
            plt.plot(test_numbers, coverage_history, color=color, linewidth=2, 
                    label=f'{circuit_name} (Final: {result["final_coverage"]:.1f}%)')
        
        plt.axhline(y=75, color='r', linestyle='--', alpha=0.7, label='75% Threshold')
        plt.axhline(y=90, color='g', linestyle='--', alpha=0.7, label='90% Threshold')
        
        plt.xlabel('Test Number')
        plt.ylabel('Fault Coverage (%)')
        plt.title('Fault Coverage vs Test Number - All Circuits')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(0, 100)
        
        if save_dir:
            plot_path = os.path.join(save_dir, 'all_circuits_coverage_plot.png')
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            print(f"Combined plot saved: {plot_path}")
        else:
            plt.show()
        
        plt.close()
    
    def save_results_to_file(self, output_file: str):
        """
        Save analysis results to a text file.
        
        Args:
            output_file: Path to the output file
        """
        if not self.results:
            print("No results available. Run analyze_all_circuits() first.")
            return
        
        with open(output_file, 'w') as f:
            f.write("RANDOM TEST VECTOR ANALYSIS RESULTS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Analysis Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Maximum Tests per Circuit: {self.max_tests}\n")
            f.write(f"Random Seed: {self.random_seed}\n\n")
            
            for circuit_name, result in self.results.items():
                f.write(f"CIRCUIT: {circuit_name}\n")
                f.write("-" * 30 + "\n")
                f.write(f"Circuit File: {result['circuit_file']}\n")
                f.write(f"Number of Inputs: {result['num_inputs']}\n")
                f.write(f"Total Possible Faults: {result['total_faults']}\n")
                f.write(f"Final Coverage: {result['final_coverage']:.2f}%\n")
                f.write(f"Final Detected Faults: {result['final_detected_faults']}\n")
                
                if result['test_75_percent'] > 0:
                    f.write(f"Tests needed for 75% coverage: {result['test_75_percent']}\n")
                else:
                    f.write("Tests needed for 75% coverage: Not achieved\n")
                
                if result['test_90_percent'] > 0:
                    f.write(f"Tests needed for 90% coverage: {result['test_90_percent']}\n")
                else:
                    f.write("Tests needed for 90% coverage: Not achieved\n")
                
                f.write("\n")
            
            # Summary table
            f.write("SUMMARY TABLE\n")
            f.write("=" * 20 + "\n")
            f.write(f"{'Circuit':<15} {'Final Coverage':<15} {'75% Tests':<12} {'90% Tests':<12}\n")
            f.write("-" * 60 + "\n")
            
            for circuit_name, result in self.results.items():
                final_cov = f"{result['final_coverage']:.1f}%"
                test_75 = str(result['test_75_percent']) if result['test_75_percent'] > 0 else "N/A"
                test_90 = str(result['test_90_percent']) if result['test_90_percent'] > 0 else "N/A"
                
                f.write(f"{circuit_name:<15} {final_cov:<15} {test_75:<12} {test_90:<12}\n")
        
        print(f"Results saved to: {output_file}")


def main():
    """Main function to run the random test analysis."""
    
    # Define circuit files
    base_dir = "/mnt/c/Users/Owner/Desktop/ECE6140/Project"
    circuit_files = [
        os.path.join(base_dir, "files", "s27.txt"),
        os.path.join(base_dir, "files", "s298f_2.txt"),
        os.path.join(base_dir, "files", "s344f_2.txt"),
        os.path.join(base_dir, "files", "s349f_2.txt")
    ]
    
    # Check if circuit files exist
    existing_circuits = []
    for circuit_file in circuit_files:
        if os.path.exists(circuit_file):
            existing_circuits.append(circuit_file)
        else:
            print(f"Warning: Circuit file not found: {circuit_file}")
    
    if not existing_circuits:
        print("No circuit files found. Exiting.")
        return
    
    # Create analyzer with fixed seed for reproducibility
    analyzer = RandomTestAnalyzer(existing_circuits, max_tests=1000, random_seed=42)
    
    # Run analysis
    results = analyzer.analyze_all_circuits()
    
    # Create plots
    output_dir = "/mnt/c/Users/Owner/Desktop/ECE6140/Project/random_test_analysis"
    analyzer.create_coverage_plots(save_dir=output_dir)
    
    # Save results
    results_file = os.path.join(output_dir, "random_test_analysis_results.txt")
    analyzer.save_results_to_file(results_file)
    
    print("\\nAnalysis complete!")
    print(f"Results saved to: {results_file}")
    print(f"Plots saved to: {output_dir}")


if __name__ == "__main__":
    main()
