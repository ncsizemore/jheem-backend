#!/usr/bin/env python3
"""
Discover available cities and scenarios in the R simulation directory
This script scans the simulation directory to find all available data combinations
"""

import os
from pathlib import Path

def discover_available_cities_and_scenarios():
    """Scan simulation directory and return available data structure"""
    
    base_dir = Path("/Users/cristina/wiley/Documents/jheem/code/jheem2_interactive/simulations/ryan-white/prerun")
    
    if not base_dir.exists():
        print(f"❌ Simulation directory not found: {base_dir}")
        return {}
    
    available_data = {}
    
    print("🔍 Scanning simulation directory for available data...")
    print(f"📂 Base directory: {base_dir}")
    print()
    
    for city_dir in base_dir.iterdir():
        if city_dir.is_dir() and city_dir.name.startswith('C.'):
            city_code = city_dir.name
            scenarios = []
            
            for scenario_file in city_dir.glob("*.Rdata"):
                scenario_name = scenario_file.stem
                scenarios.append(scenario_name)
            
            if scenarios:  # Only include cities with scenario data
                available_data[city_code] = sorted(scenarios)
    
    print("📊 Available Cities and Scenarios:")
    print("=" * 60)
    
    total_combinations = 0
    for city, scenarios in sorted(available_data.items()):
        print(f"🏙️  {city: