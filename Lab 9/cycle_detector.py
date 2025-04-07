#!/usr/bin/env python3
"""
A simpler script focused only on detecting and explaining cyclic dependencies.
"""
import json
import os
import sys
import time

# Setup path to avoid circular imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys_path_copy = sys.path.copy()
sys.path = [p for p in sys.path if p != current_dir and p != '']

try:
    import networkx as nx
    from tabulate import tabulate
except ImportError as e:
    # Restore path before reporting error
    sys.path = sys_path_copy
    print(f"Error importing dependencies: {e}")
    print("Make sure required packages are installed: networkx, tabulate")
    sys.exit(1)

# Restore original path
sys.path = sys_path_copy

def detect_cycles(dependency_file):
    """
    Detect and analyze cyclic dependencies in the given dependency file.
    """
    with open(dependency_file, 'r') as f:
        dependencies = json.load(f)
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes and edges
    for module_name in dependencies.keys():
        G.add_node(module_name)
    
    for module_name, module_data in dependencies.items():
        for imported_module in module_data.get("imports", []):
            G.add_edge(module_name, imported_module)
    
    # Find simple cycles
    start_time = time.time()
    print("Finding cyclic dependencies...")
    cycles = list(nx.simple_cycles(G))
    end_time = time.time()
    print(f"Cycle detection completed in {end_time - start_time:.2f} seconds\n")
    
    if not cycles:
        print("No cyclic dependencies detected. Great job!")
        return
    
    # Group cycles by length
    cycles_by_length = {}
    for cycle in cycles:
        length = len(cycle)
        if length not in cycles_by_length:
            cycles_by_length[length] = []
        cycles_by_length[length].append(cycle)
    
    # Print summary
    print(f"Found {len(cycles)} cyclic dependencies.")
    for length, cycles_list in sorted(cycles_by_length.items()):
        print(f"  - {len(cycles_list)} cycles of length {length}")
    print()
    
    # Print details of each cycle
    print("=== Cycle Details ===")
    for i, cycle in enumerate(sorted(cycles, key=len), 1):
        cycle_str = " → ".join(cycle)
        print(f"Cycle {i}: {cycle_str} → {cycle[0]}")
        
        # For each module in the cycle, show what they import from the cycle
        for j, module in enumerate(cycle):
            next_module = cycle[(j + 1) % len(cycle)]
            if module in dependencies and next_module in dependencies[module].get("imports", []):
                print(f"  - {module} imports {next_module}")
        print()
    
    # Find modules involved in the most cycles
    modules_in_cycles = {}
    for cycle in cycles:
        for module in cycle:
            if module not in modules_in_cycles:
                modules_in_cycles[module] = 0
            modules_in_cycles[module] += 1
    
    # Print the most problematic modules
    print("=== Most Problematic Modules ===")
    print("These modules are involved in the most cyclic dependencies:")
    problematic_modules = sorted(modules_in_cycles.items(), key=lambda x: x[1], reverse=True)
    table = [[module, count, 
              len(dependencies.get(module, {}).get("imports", [])), 
              len(dependencies.get(module, {}).get("imported_by", []))] 
             for module, count in problematic_modules[:10]]
    headers = ["Module", "Cycles Involved", "Fan-Out", "Fan-In"]
    print(tabulate(table, headers=headers, tablefmt="grid"))
    
    # Generate recommendations
    print("\n=== Recommendations for Breaking Cycles ===")
    
    # Find modules that appear in multiple cycles - these are good targets for refactoring
    if problematic_modules:
        most_problematic = problematic_modules[0][0]
        cycle_count = problematic_modules[0][1]
        print(f"1. Focus on refactoring '{most_problematic}' which is involved in {cycle_count} cycles.")
        print(f"   Consider extracting its functionality into smaller, more focused modules.")
    
    # Look for shortest cycles - these might be easier to break
    shortest_cycles = sorted(cycles, key=len)
    if shortest_cycles:
        shortest = shortest_cycles[0]
        print(f"2. Start by breaking the simplest cycle: {' → '.join(shortest)} → {shortest[0]}")
        print("   This might be easier to fix than longer, more complex cycles.")
    
    # Suggest architectural patterns
    print("3. Consider these strategies for breaking cyclic dependencies:")
    print("   - Create interfaces to implement dependency inversion")
    print("   - Extract shared functionality to separate modules")
    print("   - Use events or callbacks instead of direct imports")
    print("   - Apply the mediator pattern to coordinate between modules")
    
    # Generate report file
    report_file = os.path.join(os.path.dirname(dependency_file), "cyclic_dependencies_report.md")
    with open(report_file, "w") as f:
        f.write("# Cyclic Dependencies Report\n\n")
        f.write(f"Analysis of {dependency_file}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"Found {len(cycles)} cyclic dependencies.\n\n")
        
        for length, cycles_list in sorted(cycles_by_length.items()):
            f.write(f"- {len(cycles_list)} cycles of length {length}\n")
        
        f.write("\n## Detailed Cycles\n\n")
        for i, cycle in enumerate(sorted(cycles, key=len), 1):
            cycle_str = " → ".join(cycle)
            f.write(f"### Cycle {i}\n\n")
            f.write(f"{cycle_str} → {cycle[0]}\n\n")
            
            # For each module in the cycle, show what they import from the cycle
            for j, module in enumerate(cycle):
                next_module = cycle[(j + 1) % len(cycle)]
                if module in dependencies and next_module in dependencies[module].get("imports", []):
                    f.write(f"- {module} imports {next_module}\n")
            f.write("\n")
        
        f.write("## Most Problematic Modules\n\n")
        f.write("| Module | Cycles Involved | Fan-Out | Fan-In |\n")
        f.write("|--------|----------------|---------|--------|\n")
        for module, count in problematic_modules[:10]:
            fan_out = len(dependencies.get(module, {}).get("imports", []))
            fan_in = len(dependencies.get(module, {}).get("imported_by", []))
            f.write(f"| {module} | {count} | {fan_out} | {fan_in} |\n")
    
    print(f"\nReport generated: {report_file}")
    return cycles

if __name__ == "__main__":
    dependency_file = os.path.join(current_dir, "dependencies.json")
    cycles = detect_cycles(dependency_file)
