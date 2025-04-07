#!/usr/bin/env python3
"""
Dependency Impact Assessment Script

Analyzes the dependency structure to determine:
1. The impact of changing each module on the rest of the system
2. Modules that are at high risk of breaking the system if modified
"""

import json
import os
import sys
from collections import defaultdict
from tabulate import tabulate
import matplotlib.pyplot as plt
import numpy as np

def load_dependencies(dependency_file):
    """Load the dependency data from JSON file"""
    with open(dependency_file, 'r') as f:
        return json.load(f)

def calculate_impact_scores(dependencies):
    """
    Calculate the impact score for each module.
    
    Impact Score: Measure of how many other modules would be affected if this module changes.
    It considers both direct and indirect dependencies.
    """
    # Initialize direct impact scores (based on fan-in)
    direct_impact = {}
    for module, data in dependencies.items():
        # Fan-in: number of modules that directly import this module
        fan_in = len(data.get('imported_by', []))
        direct_impact[module] = fan_in
    
    # Calculate transitive impact (modules that indirectly depend on this module)
    transitive_impact = defaultdict(set)
    
    # For each module that has importers
    for module in dependencies:
        # Get direct importers
        direct_importers = set(dependencies[module].get('imported_by', []))
        
        # Initialize the set of all affected modules with direct importers
        all_affected = direct_importers.copy()
        
        # Keep track of modules to process
        to_process = direct_importers.copy()
        processed = set()
        
        # Find all modules that indirectly import this module
        while to_process:
            importer = to_process.pop()
            processed.add(importer)
            
            # Find modules that import this importer
            if importer in dependencies:
                next_level = set(dependencies[importer].get('imported_by', []))
                # Add new dependencies to processing queue
                new_deps = next_level - processed - to_process
                to_process.update(new_deps)
                all_affected.update(new_deps)
        
        # Store all affected modules (both direct and indirect)
        transitive_impact[module] = all_affected
    
    # Calculate final impact scores
    impact_scores = []
    for module in dependencies:
        direct_count = len(dependencies[module].get('imported_by', []))
        transitive_count = len(transitive_impact[module])
        
        # Don't count direct importers twice in transitive count
        indirect_count = transitive_count - direct_count
        
        # Total impact score: weighted sum of direct and indirect impact
        # Direct dependencies are given higher weight as they're more immediately affected
        total_impact = (direct_count * 2) + indirect_count
        
        impact_scores.append({
            'module': module,
            'direct_impact': direct_count,
            'indirect_impact': indirect_count,
            'total_impact': total_impact
        })
    
    # Sort by total impact
    impact_scores.sort(key=lambda x: x['total_impact'], reverse=True)
    return impact_scores

def calculate_risk_scores(dependencies):
    """
    Calculate risk scores for each module.
    
    Risk Score: Measure of how likely a module is to break the system if modified.
    Considers:
    - Coupling (both fan-in and fan-out)
    - Whether the module is part of a cyclic dependency
    - Whether the module is a core module (determined by usage/centrality)
    """
    # Calculate module coupling (fan-in * fan-out)
    coupling_scores = []
    for module, data in dependencies.items():
        fan_in = len(data.get('imported_by', []))
        fan_out = len(data.get('imports', []))
        coupling = fan_in * fan_out
        coupling_scores.append({
            'module': module,
            'fan_in': fan_in,
            'fan_out': fan_out,
            'coupling': coupling
        })
    
    # Detect cyclic dependencies
    has_cycles = detect_cycles(dependencies)
    
    # Calculate centrality (how central a module is in the dependency graph)
    centrality_scores = calculate_centrality(dependencies)
    
    # Combine all factors for a final risk score
    risk_scores = []
    for module in dependencies:
        # Find coupling score for this module
        coupling = next((score['coupling'] for score in coupling_scores 
                         if score['module'] == module), 0)
        
        # Check if module is in a cycle
        in_cycle = module in has_cycles
        cycle_factor = 2 if in_cycle else 1  # Double risk for modules in cycles
        
        # Get centrality score
        centrality = centrality_scores.get(module, 0)
        
        # Calculate final risk score
        # Formula: (coupling * cycle_factor * centrality_weight)
        risk_score = coupling * cycle_factor * (centrality + 1)
        
        fan_in = len(dependencies[module].get('imported_by', []))
        fan_out = len(dependencies[module].get('imports', []))
        
        risk_scores.append({
            'module': module,
            'fan_in': fan_in,
            'fan_out': fan_out,
            'coupling': coupling,
            'in_cycle': in_cycle,
            'centrality': centrality,
            'risk_score': risk_score
        })
    
    # Sort by risk score
    risk_scores.sort(key=lambda x: x['risk_score'], reverse=True)
    return risk_scores

def detect_cycles(dependencies):
    """Detect which modules are part of cyclic dependencies"""
    # This is a simplified cycle detection
    # For a more comprehensive detection, use the networkx library
    modules_in_cycles = set()
    
    # For each module
    for module, data in dependencies.items():
        # Check if any of its imports also import it (direct cycle)
        imports = data.get('imports', [])
        for imported in imports:
            if imported in dependencies and module in dependencies[imported].get('imported_by', []):
                modules_in_cycles.add(module)
                modules_in_cycles.add(imported)
    
    return modules_in_cycles

def calculate_centrality(dependencies):
    """
    Calculate a simple centrality score for each module.
    Higher score means the module is more central to the system.
    """
    centrality = {}
    
    for module in dependencies:
        # Count how many paths go through this module
        # (simplified: count how many modules both import and are imported by this module)
        importers = set(dependencies[module].get('imported_by', []))
        imports = set(dependencies[module].get('imports', []))
        
        direct_connections = len(importers) + len(imports)
        
        # Modules that this module helps connect (those it imports that also import its importers)
        connections = 0
        for imported in imports:
            if imported in dependencies:
                for importer in importers:
                    if importer in dependencies[imported].get('imported_by', []):
                        connections += 1
        
        centrality[module] = connections + direct_connections
    
    # Normalize to range 0-10
    if centrality:
        max_value = max(centrality.values())
        if max_value > 0:
            for module in centrality:
                centrality[module] = (centrality[module] / max_value) * 10
    
    return centrality

def generate_report(impact_scores, risk_scores, dependencies, output_dir):
    """Generate a comprehensive impact and risk assessment report"""
    # Table formats for better readability
    table_format = "grid"
    
    # 1. Create text report
    report_path = os.path.join(output_dir, "dependency_impact_report.md")
    with open(report_path, 'w') as f:
        f.write("# Dependency Impact Assessment Report\n\n")
        
        # Include summary statistics
        f.write("## Summary\n\n")
        f.write(f"- Total modules analyzed: {len(dependencies)}\n")
        f.write(f"- High impact modules (impact score > 20): {len([m for m in impact_scores if m['total_impact'] > 20])}\n")
        f.write(f"- High risk modules (risk score > 100): {len([m for m in risk_scores if m['risk_score'] > 100])}\n\n")
        
        # Impact assessment
        f.write("## Impact Assessment\n\n")
        f.write("The following modules have the highest impact on the rest of the system. Changes to these modules will affect many other parts of the codebase.\n\n")
        
        # Impact table
        impact_table = []
        for score in impact_scores[:15]:  # Top 15 by impact
            impact_table.append([
                score['module'],
                score['direct_impact'],
                score['indirect_impact'],
                score['total_impact']
            ])
        
        f.write("### Top 15 Modules by Impact\n\n")
        f.write("| Module | Direct Impact | Indirect Impact | Total Impact Score |\n")
        f.write("|--------|--------------|----------------|------------------|\n")
        for row in impact_table:
            f.write(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n")
        
        # Risk assessment
        f.write("\n## Risk Assessment\n\n")
        f.write("The following modules are at the highest risk of breaking the system if modified. These are typically highly coupled, in cyclic dependencies, or central to the system architecture.\n\n")
        
        # Risk table
        risk_table = []
        for score in risk_scores[:15]:  # Top 15 by risk
            risk_table.append([
                score['module'],
                score['fan_in'],
                score['fan_out'],
                score['coupling'],
                'Yes' if score['in_cycle'] else 'No',
                f"{score['centrality']:.1f}",
                f"{score['risk_score']:.1f}"
            ])
        
        f.write("### Top 15 Modules by Risk\n\n")
        f.write("| Module | Fan-In | Fan-Out | Coupling | In Cycle | Centrality | Risk Score |\n")
        f.write("|--------|--------|---------|----------|----------|------------|------------|\n")
        for row in risk_table:
            f.write(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} |\n")
        
        # Recommended approach for changes
        f.write("\n## Recommendations for Making Changes\n\n")
        
        f.write("### High-Impact Modules\n\n")
        f.write("When modifying high-impact modules:\n\n")
        f.write("1. **Plan carefully** - Changes will have wide-ranging effects\n")
        f.write("2. **Thoroughly test dependent modules** - Test not just the module you changed, but also modules that depend on it\n")
        f.write("3. **Consider deprecation periods** for interface changes\n")
        f.write("4. **Document changes extensively** to help dependent module maintainers\n\n")
        
        f.write("### High-Risk Modules\n\n")
        f.write("When modifying high-risk modules:\n\n")
        f.write("1. **Use extra caution** - These modules are most likely to cause system breakage\n")
        f.write("2. **Consider refactoring** to reduce coupling and break cycles before making functional changes\n")
        f.write("3. **Create comprehensive tests** before making changes\n")
        f.write("4. **Review changes** with team members familiar with the module\n\n")
        
        # Specific modules report
        top_impact = impact_scores[0]['module'] if impact_scores else None
        top_risk = risk_scores[0]['module'] if risk_scores else None
        
        if top_impact:
            f.write(f"## Deep Dive: Highest Impact Module - {top_impact}\n\n")
            direct_importers = dependencies[top_impact].get('imported_by', [])
            f.write(f"The module `{top_impact}` is directly imported by {len(direct_importers)} other modules:\n\n")
            for importer in direct_importers:
                f.write(f"- {importer}\n")
            f.write("\nChanges to this module will cascade through these dependencies and their dependents.\n\n")
        
        if top_risk and top_risk != top_impact:
            f.write(f"## Deep Dive: Highest Risk Module - {top_risk}\n\n")
            f.write("This module is high risk because:\n\n")
            top_score = next(score for score in risk_scores if score['module'] == top_risk)
            if top_score['in_cycle']:
                f.write("- It is part of one or more dependency cycles\n")
            f.write(f"- It has high coupling (fan-in × fan-out = {top_score['coupling']})\n")
            if top_score['centrality'] > 5:
                f.write(f"- It is central to the system architecture (centrality score: {top_score['centrality']:.1f})\n")
            f.write("\nModifying this module requires extreme caution and thorough testing.\n")
    
    # 2. Create visualizations
    
    # Impact visualization
    plt.figure(figsize=(12, 8))
    modules = [score['module'].split('.')[-1] for score in impact_scores[:15]]  # Use last part of module name
    direct = [score['direct_impact'] for score in impact_scores[:15]]
    indirect = [score['indirect_impact'] for score in impact_scores[:15]]
    
    x = np.arange(len(modules))
    width = 0.35
    
    plt.bar(x - width/2, direct, width, label='Direct Impact')
    plt.bar(x + width/2, indirect, width, label='Indirect Impact')
    
    plt.xlabel('Modules')
    plt.ylabel('Impact Score')
    plt.title('Impact of Changes by Module')
    plt.xticks(x, modules, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    
    impact_chart_path = os.path.join(output_dir, "impact_assessment_chart.png")
    plt.savefig(impact_chart_path)
    
    # Risk visualization
    plt.figure(figsize=(12, 8))
    modules = [score['module'].split('.')[-1] for score in risk_scores[:15]]  # Use last part of module name
    risk_scores_values = [score['risk_score'] for score in risk_scores[:15]]
    
    colors = ['red' if score['in_cycle'] else 'orange' for score in risk_scores[:15]]
    
    plt.bar(modules, risk_scores_values, color=colors)
    plt.xlabel('Modules')
    plt.ylabel('Risk Score')
    plt.title('Risk Assessment by Module (Red indicates cyclic dependency)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    risk_chart_path = os.path.join(output_dir, "risk_assessment_chart.png")
    plt.savefig(risk_chart_path)
    
    return report_path, impact_chart_path, risk_chart_path

def main():
    """Main function to run the assessment"""
    # Get the project directory
    project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uvicorn", "uvicorn")
    dependency_file = os.path.join(project_dir, "dependencies.json")
    
    if not os.path.exists(dependency_file):
        print(f"Error: Dependency file not found at {dependency_file}")
        return

    print("Loading dependencies...")
    dependencies = load_dependencies(dependency_file)
    
    print("Calculating impact scores...")
    impact_scores = calculate_impact_scores(dependencies)
    
    print("Calculating risk scores...")
    risk_scores = calculate_risk_scores(dependencies)
    
    # Print results to console
    print("\n=== DEPENDENCY IMPACT ASSESSMENT ===\n")
    
    print("Top 10 Modules by Impact:")
    table_data = [[
        score['module'], 
        score['direct_impact'],
        score['indirect_impact'],
        score['total_impact']
    ] for score in impact_scores[:10]]
    print(tabulate(table_data, 
                  headers=["Module", "Direct Impact", "Indirect Impact", "Total Impact"],
                  tablefmt="grid"))
    print()
    
    print("Top 10 Modules by Risk:")
    table_data = [[
        score['module'],
        score['fan_in'],
        score['fan_out'],
        'Yes' if score['in_cycle'] else 'No',
        f"{score['centrality']:.1f}",
        f"{score['risk_score']:.1f}"
    ] for score in risk_scores[:10]]
    print(tabulate(table_data, 
                  headers=["Module", "Fan-In", "Fan-Out", "In Cycle", "Centrality", "Risk Score"],
                  tablefmt="grid"))
    print()
    
    # Generate comprehensive report
    output_dir = os.path.dirname(os.path.abspath(__file__))
    report_path, impact_chart, risk_chart = generate_report(
        impact_scores, risk_scores, dependencies, output_dir)
    
    print(f"Report generated: {report_path}")
    print(f"Impact chart: {impact_chart}")
    print(f"Risk chart: {risk_chart}")
    
    # Provide specific advice for high-impact and high-risk modules
    if impact_scores:
        print(f"\nHighest Impact Module: {impact_scores[0]['module']}")
        print(f"  - Direct Impact: {impact_scores[0]['direct_impact']} modules")
        print(f"  - Indirect Impact: {impact_scores[0]['indirect_impact']} modules")
        print("  - Changes to this module will affect the most other modules in the system.")
    
    if risk_scores:
        print(f"\nHighest Risk Module: {risk_scores[0]['module']}")
        if risk_scores[0]['in_cycle']:
            print("  - This module is part of a cyclic dependency")
        print(f"  - Coupling Score: {risk_scores[0]['coupling']}")
        print("  - This module has the highest chance of breaking the system if modified.")

if __name__ == "__main__":
    main()
