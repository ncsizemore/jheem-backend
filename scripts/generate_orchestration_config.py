#!/usr/bin/env python3
"""
Generate orchestration configuration for JHEEM plot generation
Creates city-based job configurations optimized for simulation reuse
"""

import yaml
import json
import argparse
from pathlib import Path

# Available data configuration - verified cities from simulation directory
AVAILABLE_CITIES = [
    "C.12060", "C.12420", "C.12580", "C.12940", "C.14460", "C.16740", 
    "C.16980", "C.17460", "C.18140", "C.19100", "C.19820", "C.26420",
    "C.26900", "C.27260", "C.29820", "C.31080", "C.32820", "C.33100",
    "C.35380", "C.35620", "C.36740", "C.37980", "C.38060", "C.40140",
    "C.40900", "C.41700", "C.41740", "C.41860", "C.42660", "C.45300",
    "C.47900"
]

SCENARIOS = ["cessation", "brief_interruption", "prolonged_interruption"]

OUTCOMES = [
    "incidence", "diagnosed.prevalence", "suppression", "testing", 
    "prep.uptake", "awareness", "rw.clients", "adap.clients", 
    "non.adap.clients", "oahs.clients", "adap.proportion", 
    "oahs.suppression", "adap.suppression", "new"
]

STATISTICS = ["mean.and.interval", "median.and.interval", "individual.simulation"]

FACETS = [
    "none", "age", "race", "sex", "risk",  # Single facets
    "age+race", "age+sex", "age+risk", "race+sex", "race+risk", "sex+risk",  # Two facets
    "age+race+sex", "age+race+risk", "age+sex+risk", "race+sex+risk",  # Three facets
    "age+race+sex+risk"  # All four facets
]

def generate_city_based_jobs(cities=None, scenarios=None, outcomes=None, statistics=None, facets=None):
    """Generate one job per city for optimal simulation reuse"""
    
    # Use provided parameters or defaults
    cities = cities or AVAILABLE_CITIES
    scenarios = scenarios or SCENARIOS  
    outcomes = outcomes or OUTCOMES
    statistics = statistics or STATISTICS
    facets = facets or FACETS
    
    jobs = []
    
    for city in cities:
        job = {
            "city": city,
            "scenarios": scenarios,
            "outcomes": outcomes,
            "statistics": statistics,
            "facets": facets
        }
        
        # Calculate expected plot count for this job
        plot_count = len(scenarios) * len(outcomes) * len(statistics) * len(facets)
        job["expected_plots"] = plot_count
        
        # Estimate execution time based on 4.05s per plot
        estimated_seconds = plot_count * 4.05
        job["estimated_hours"] = round(estimated_seconds / 3600, 2)
        
        jobs.append(job)
    
    return jobs

def generate_test_subset_config():
    """Generate a test configuration with subset of data for validation"""
    # Test with 4 cities, limited outcomes/facets for manageable testing
    test_cities = ["C.12580", "C.12940", "C.14460", "C.16740"]
    test_outcomes = ["incidence", "diagnosed.prevalence", "adap.proportion"]
    test_statistics = ["mean.and.interval"]
    test_facets = ["none", "sex", "age"]
    
    return generate_city_based_jobs(
        cities=test_cities,
        outcomes=test_outcomes, 
        statistics=test_statistics,
        facets=test_facets
    )

def generate_minimal_test_config():
    """Generate ultra-minimal configuration for initial integration testing (1 plot)"""
    # Single city, single scenario, single outcome, single statistic, single facet
    minimal_cities = ["C.12580"]
    minimal_scenarios = ["cessation"]
    minimal_outcomes = ["incidence"] 
    minimal_statistics = ["mean.and.interval"]
    minimal_facets = ["none"]
    
    return generate_city_based_jobs(
        cities=minimal_cities,
        scenarios=minimal_scenarios,
        outcomes=minimal_outcomes,
        statistics=minimal_statistics,
        facets=minimal_facets
    )

def generate_medium_subset_config():
    """Generate a medium-scale configuration for serious testing (~1000 plots)"""
    # Use 6 cities with more outcomes but limited statistics/facets
    medium_cities = ["C.12580", "C.12940", "C.14460", "C.16740", "C.19100", "C.26420"]
    medium_outcomes = ["incidence", "diagnosed.prevalence", "adap.proportion", "suppression", "prep.uptake"]
    medium_statistics = ["mean.and.interval", "median.and.interval"]
    medium_facets = ["none", "sex", "age", "race", "sex+age"]
    
    return generate_city_based_jobs(
        cities=medium_cities,
        outcomes=medium_outcomes,
        statistics=medium_statistics, 
        facets=medium_facets
    )

def generate_orchestration_config(config_type="test", output_dir="orchestration_configs"):
    """Generate complete orchestration configuration"""
    Path(output_dir).mkdir(exist_ok=True)
    
    if config_type == "minimal":
        jobs = generate_minimal_test_config()
    elif config_type == "test":
        jobs = generate_test_subset_config()
    elif config_type == "medium":
        jobs = generate_medium_subset_config()
    elif config_type == "full":
        jobs = generate_city_based_jobs()
    else:
        raise ValueError(f"Unknown config_type: {config_type}")
    
    # Overall configuration
    config = {
        "strategy": "city_based_chunking",
        "config_type": config_type,
        "total_jobs": len(jobs),
        "total_expected_plots": sum(job["expected_plots"] for job in jobs),
        "estimated_total_hours": sum(job["estimated_hours"] for job in jobs),
        "estimated_parallel_hours": max(job["estimated_hours"] for job in jobs),
        "jobs": jobs
    }
    
    # Save master configuration
    config_file = f"{output_dir}/master_config_{config_type}.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    # Generate individual job files for easy execution
    for i, job in enumerate(jobs):
        job_config = {"jobs": [job]}
        job_file = f"{output_dir}/job_{config_type}_{i+1:02d}_{job['city']}.yaml"
        with open(job_file, "w") as f:
            yaml.dump(job_config, f, default_flow_style=False)
    
    print(f"Generated {config_type} orchestration configuration:")
    print(f"  - Total jobs: {config['total_jobs']}")
    print(f"  - Total plots: {config['total_expected_plots']:,}")
    print(f"  - Sequential time: {config['estimated_total_hours']:.1f} hours")
    print(f"  - Parallel time: {config['estimated_parallel_hours']:.1f} hours")
    print(f"  - Config files: {output_dir}/")
    print(f"  - Master config: {config_file}")
    
    return config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate orchestration configurations for plot generation")
    parser.add_argument("--type", choices=["minimal", "test", "medium", "full"], default="test",
                       help="Configuration type: minimal (1 plot), test (~100 plots), medium (~1000 plots), full (~64K plots)")
    parser.add_argument("--output-dir", default="orchestration_configs", 
                       help="Output directory for configuration files")
    
    args = parser.parse_args()
    
    generate_orchestration_config(args.type, args.output_dir)
