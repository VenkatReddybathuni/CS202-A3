import json
import os
import sys

# Move matplotlib import after we modify sys.path to avoid circular imports
current_dir = os.path.dirname(os.path.abspath(__file__))
# Temporarily remove the current directory from path to avoid circular imports
if current_dir in sys.path:
    sys.path.remove(current_dir)

# Now import matplotlib and other dependencies
import matplotlib.pyplot as plt
from tabulate import tabulate
from PIL import Image

# Restore the path
sys.path.insert(0, current_dir)

# Load the JSON file
with open(os.path.join(current_dir, "dependencies.json"), "r") as f:
    dependencies = json.load(f)

# Initialize lists to store module data
modules = []
fan_ins = []
fan_outs = []

# Calculate fan-in and fan-out for each module
for module_name, module_data in dependencies.items():
    # Fan-out is the number of imports
    fan_out = len(module_data.get("imports", []))
    
    # Fan-in is the number of modules that import this module
    fan_in = len(module_data.get("imported_by", []))
    
    modules.append(module_name)
    fan_ins.append(fan_in)
    fan_outs.append(fan_out)

# Prepare data for tabulation
table_data = []
for i, module in enumerate(modules):
    table_data.append([module, fan_outs[i], fan_ins[i]])

# Sort the table data by module name
table_data.sort(key=lambda x: x[0])

# Convert to tabulated text
table_str = tabulate(table_data, headers=["Module", "Fan-Out", "Fan-In"], tablefmt="grid")

print(table_str)

# Configure plot
plt.figure(figsize=(10, len(table_data) * 0.4))  # Adjust height based on number of rows
plt.text(0, 1, table_str, fontsize=10, family="monospace", verticalalignment="top")

plt.axis("off")  # Hide axes
plt.tight_layout()

# Save as image
image_path = os.path.join(current_dir, "dependency_table.png")
plt.savefig(image_path, bbox_inches="tight", dpi=300)
print(f"Table saved as {image_path}")

# Create a fan-in vs fan-out scatter plot
plt.figure(figsize=(10, 8))
plt.scatter(fan_ins, fan_outs, alpha=0.6)

# Add labels to points
for i, module in enumerate(modules):
    plt.annotate(module, (fan_ins[i], fan_outs[i]), fontsize=8)

plt.title("Fan-In vs Fan-Out Analysis")
plt.xlabel("Fan-In (Number of modules importing this module)")
plt.ylabel("Fan-Out (Number of modules imported by this module)")
plt.grid(True, linestyle='--', alpha=0.7)

# Save scatter plot
scatter_path = os.path.join(current_dir, "fan_analysis_scatter.png")
plt.savefig(scatter_path, bbox_inches="tight", dpi=300)
print(f"Scatter plot saved as {scatter_path}")
