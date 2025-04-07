import json
import os
import sys

# Setup path to avoid circular imports - crucial for preventing the logging module conflict
current_dir = os.path.dirname(os.path.abspath(__file__))
# Remove current dir from path to avoid importing local logging.py when networkx tries to import logging
sys_path_copy = sys.path.copy()
sys.path = [p for p in sys.path if p != current_dir and p != '']

# Now import dependencies after path modification
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import numpy as np
    from tabulate import tabulate
    from collections import defaultdict
except ImportError as e:
    # Restore path before reporting error
    sys.path = sys_path_copy
    print(f"Error importing dependencies: {e}")
    print("Make sure required packages are installed: networkx, matplotlib, numpy, tabulate")
    sys.exit(1)

# Restore original path after imports
sys.path = sys_path_copy

# Load the dependency data
with open(os.path.join(current_dir, "dependencies.json"), "r") as f:
    dependencies = json.load(f)

# Create a directed graph
G = nx.DiGraph()

# Add nodes (modules)
for module_name in dependencies.keys():
    G.add_node(module_name)

# Add edges (dependencies)
for module_name, module_data in dependencies.items():
    for imported_module in module_data.get("imports", []):
        G.add_edge(module_name, imported_module)

print("=== Dependency Analysis ===\n")

# 1. Calculate Coupling Metrics
coupling_metrics = []
for module_name, module_data in dependencies.items():
    fan_in = len(module_data.get("imported_by", []))
    fan_out = len(module_data.get("imports", []))
    coupling = fan_in * fan_out  # A simple coupling metric
    
    coupling_metrics.append({
        "module": module_name,
        "fan_in": fan_in,
        "fan_out": fan_out,
        "coupling": coupling
    })

# Sort by coupling score
coupling_metrics.sort(key=lambda x: x["coupling"], reverse=True)

# Display top 10 most coupled modules
print("Top 10 Most Coupled Modules:")
table_data = [[m["module"], m["fan_in"], m["fan_out"], m["coupling"]] 
              for m in coupling_metrics[:10]]
print(tabulate(table_data, 
              headers=["Module", "Fan-In", "Fan-Out", "Coupling Score"],
              tablefmt="grid"))
print("\n")

# Save coupling data to CSV
with open(os.path.join(current_dir, "coupling_metrics.csv"), "w") as f:
    f.write("Module,Fan-In,Fan-Out,Coupling Score\n")
    for m in coupling_metrics:
        f.write(f"{m['module']},{m['fan_in']},{m['fan_out']},{m['coupling']}\n")

# 2. Detect Cyclic Dependencies
print("Cyclic Dependencies Analysis:")
cycles = list(nx.simple_cycles(G))

if not cycles:
    print("No cyclic dependencies detected.")
else:
    print(f"Found {len(cycles)} cyclic dependencies:")
    for i, cycle in enumerate(cycles, 1):
        cycle_str = " -> ".join(cycle)
        print(f"Cycle {i}: {cycle_str} -> {cycle[0]}")
        
        # Identify modules involved in cycles
        for module in cycle:
            # Mark modules that are part of cycles
            for m in coupling_metrics:
                if m["module"] == module:
                    m["in_cycle"] = True
print("\n")

# 3. Identify Unused and Disconnected Modules
print("Unused and Disconnected Modules:")
isolated_nodes = list(nx.isolates(G))
if isolated_nodes:
    print(f"Found {len(isolated_nodes)} isolated modules:")
    for node in isolated_nodes:
        print(f"  - {node}")
else:
    print("No isolated modules found.")

# Check for modules with no fan-in (not imported by any other module)
no_fan_in = [module for module, data in dependencies.items() 
             if not data.get("imported_by", [])]
if no_fan_in:
    print(f"\nModules not imported by any other module (no fan-in): {len(no_fan_in)}")
    for module in no_fan_in:
        print(f"  - {module}")

# Check for modules with no fan-out (not importing any other module)
no_fan_out = [module for module, data in dependencies.items() 
              if not data.get("imports", [])]
if no_fan_out:
    print(f"\nModules not importing any other module (no fan-out): {len(no_fan_out)}")
    for module in no_fan_out:
        print(f"  - {module}")
print("\n")

# 4. Assess the Dependency Depth
print("Dependency Depth Analysis:")

# Calculate longest paths
try:
    # Make a copy of G without cycles for longest path calculation
    DAG = nx.DiGraph(G)
    cycles_edges = set()
    for cycle in cycles:
        for i in range(len(cycle)):
            cycles_edges.add((cycle[i], cycle[(i+1) % len(cycle)]))
    
    for edge in cycles_edges:
        if DAG.has_edge(*edge):
            DAG.remove_edge(*edge)
    
    # Find all roots (nodes with no incoming edges)
    roots = [n for n in DAG.nodes() if DAG.in_degree(n) == 0]
    
    # Find all leaves (nodes with no outgoing edges)
    leaves = [n for n in DAG.nodes() if DAG.out_degree(n) == 0]
    
    # Find the longest path
    longest_path = None
    longest_length = 0
    
    for root in roots:
        for leaf in leaves:
            try:
                path = nx.shortest_path(DAG, root, leaf)
                if len(path) > longest_length:
                    longest_length = len(path)
                    longest_path = path
            except nx.NetworkXNoPath:
                pass
    
    if longest_path:
        print(f"Maximum dependency depth: {longest_length - 1}")
        print(f"Longest dependency chain: {' -> '.join(longest_path)}")
    else:
        print("Could not determine the longest dependency chain.")
except Exception as e:
    print(f"Error calculating dependency depth: {e}")
print("\n")

# 5. Module Categorization
print("Module Categorization:")

# Categorize modules
stable_abstractions = []
unstable_abstractions = []
stable_concretions = []
unstable_concretions = []

# Define thresholds
fan_in_threshold = 5  # High fan-in
fan_out_threshold = 5  # High fan-out

for m in coupling_metrics:
    if m["fan_in"] >= fan_in_threshold and m["fan_out"] < fan_out_threshold:
        stable_abstractions.append(m["module"])
    elif m["fan_in"] >= fan_in_threshold and m["fan_out"] >= fan_out_threshold:
        unstable_abstractions.append(m["module"])
    elif m["fan_in"] < fan_in_threshold and m["fan_out"] < fan_out_threshold:
        stable_concretions.append(m["module"])
    else:  # Low fan-in, high fan-out
        unstable_concretions.append(m["module"])

print(f"Stable Abstractions (high fan-in, low fan-out): {len(stable_abstractions)}")
for module in stable_abstractions[:5]:
    print(f"  - {module}")
if len(stable_abstractions) > 5:
    print(f"  - ... and {len(stable_abstractions) - 5} more")

print(f"\nUnstable Abstractions (high fan-in, high fan-out): {len(unstable_abstractions)}")
for module in unstable_abstractions[:5]:
    print(f"  - {module}")
if len(unstable_abstractions) > 5:
    print(f"  - ... and {len(unstable_abstractions) - 5} more")

print(f"\nStable Concretions (low fan-in, low fan-out): {len(stable_concretions)}")
for module in stable_concretions[:5]:
    print(f"  - {module}")
if len(stable_concretions) > 5:
    print(f"  - ... and {len(stable_concretions) - 5} more")

print(f"\nUnstable Concretions (low fan-in, high fan-out): {len(unstable_concretions)}")
for module in unstable_concretions[:5]:
    print(f"  - {module}")
if len(unstable_concretions) > 5:
    print(f"  - ... and {len(unstable_concretions) - 5} more")

# 6. Visualize Core Dependencies
print("\n=== Creating Visualizations ===")

# Create a visualization of the top coupled modules
plt.figure(figsize=(12, 10))

# Only visualize the most important dependencies
top_n = 15
top_modules = [m["module"] for m in coupling_metrics[:top_n]]
subgraph = G.subgraph(top_modules)

# Use a layout that works well for directed graphs
pos = nx.spring_layout(subgraph, seed=42, k=0.8)

# Draw nodes with size proportional to coupling
node_sizes = [coupling_metrics[coupling_metrics.index(next(m for m in coupling_metrics if m["module"] == node))]["coupling"] * 10 + 100 for node in subgraph.nodes()]

# Draw the graph
nx.draw_networkx_nodes(subgraph, pos, node_color='skyblue', 
                      node_size=node_sizes, alpha=0.8)
nx.draw_networkx_edges(subgraph, pos, edge_color='gray', 
                      width=1, alpha=0.5, arrows=True, arrowsize=15)
nx.draw_networkx_labels(subgraph, pos, font_size=10)

plt.title(f"Dependencies Between Top {top_n} Most Coupled Modules")
plt.axis('off')
plt.tight_layout()

# Save the visualization
core_deps_path = os.path.join(current_dir, "core_dependencies.png")
plt.savefig(core_deps_path, bbox_inches="tight", dpi=300)
print(f"Core dependencies visualization saved as {core_deps_path}")

# 7. Create a metrics summary report
print("\nGenerating dependency metrics summary report...")

with open(os.path.join(current_dir, "dependency_metrics_summary.txt"), "w") as f:
    f.write("DEPENDENCY METRICS SUMMARY\n")
    f.write("==========================\n\n")
    
    f.write(f"Total modules: {len(dependencies)}\n")
    f.write(f"Total dependencies: {G.number_of_edges()}\n")
    
    if cycles:
        f.write(f"Cyclic dependencies: {len(cycles)}\n")
    else:
        f.write("Cyclic dependencies: None\n")
    
    f.write(f"Isolated modules: {len(isolated_nodes)}\n")
    f.write(f"Modules with no imports (fan-out=0): {len(no_fan_out)}\n")
    f.write(f"Modules not imported (fan-in=0): {len(no_fan_in)}\n\n")
    
    f.write("Module Categorization:\n")
    f.write(f"- Stable Abstractions: {len(stable_abstractions)}\n")
    f.write(f"- Unstable Abstractions: {len(unstable_abstractions)}\n")
    f.write(f"- Stable Concretions: {len(stable_concretions)}\n")
    f.write(f"- Unstable Concretions: {len(unstable_concretions)}\n\n")
    
    # Calculate averages
    avg_fan_in = sum(m["fan_in"] for m in coupling_metrics) / len(coupling_metrics)
    avg_fan_out = sum(m["fan_out"] for m in coupling_metrics) / len(coupling_metrics)
    avg_coupling = sum(m["coupling"] for m in coupling_metrics) / len(coupling_metrics)
    
    f.write("Averages:\n")
    f.write(f"- Average Fan-In: {avg_fan_in:.2f}\n")
    f.write(f"- Average Fan-Out: {avg_fan_out:.2f}\n")
    f.write(f"- Average Coupling Score: {avg_coupling:.2f}\n")

print("Analysis complete! Check the generated files for results.")
