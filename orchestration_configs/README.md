# Orchestration Configuration Templates
# Use the config generator to create actual configs from these templates

# Generate test configuration (4 cities, ~100 plots)
# python scripts/generate_orchestration_config.py --type test

# Generate medium configuration (6 cities, ~900 plots)  
# python scripts/generate_orchestration_config.py --type medium

# Generate full configuration (31 cities, ~64K plots)
# python scripts/generate_orchestration_config.py --type full

# Example usage:
# python scripts/local_orchestration.py orchestration_configs/master_config_test.yaml --max-parallel 2
