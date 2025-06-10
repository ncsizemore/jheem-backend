#!/usr/bin/env python3
"""
Script to register existing plots in DynamoDB
This populates the database with metadata for plots that already exist in S3
"""

import boto3
import json
import os
from datetime import datetime

def register_existing_plots():
    """Register the 3 existing plots in DynamoDB"""
    
    # Initialize DynamoDB client for LocalStack
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://localhost:4566',
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name='us-east-1'
    )
    
    table_name = 'jheem-plot-metadata-local'
    table = dynamodb.Table(table_name)
    
    # Define the existing plots
    existing_plots = [
        {
            'city': 'C.12580',
            'scenario': 'cessation',
            'outcome': 'incidence',
            'statistic_type': 'mean.and.interval',
            'facet_choice': 'sex',
            's3_key': 'plots/jheem_real_plot.json',
            'file_size': 32768,
            'created_at': '2025-06-10T20:00:00Z'
        },
        {
            'city': 'C.12580',
            'scenario': 'cessation',
            'outcome': 'diagnosed.prevalence',
            'statistic_type': 'mean.and.interval',
            'facet_choice': 'sex',
            's3_key': 'plots/prevalence_test.json',
            'file_size': 28500,
            'created_at': '2025-06-10T21:00:00Z'
        },
        {
            'city': 'C.12580',
            'scenario': 'cessation',
            'outcome': 'adap.proportion',
            'statistic_type': 'mean.and.interval',
            'facet_choice': 'sex',
            's3_key': 'plots/adap_proportion_test.json',
            'file_size': 25600,
            'created_at': '2025-06-10T21:30:00Z'
        }
    ]
    
    print(f"Registering {len(existing_plots)} plots in DynamoDB table: {table_name}")
    
    for plot_info in existing_plots:
        # Create composite keys
        city_scenario = f"{plot_info['city']}#{plot_info['scenario']}"
        outcome_stat_facet = f"{plot_info['outcome']}#{plot_info['statistic_type']}#{plot_info['facet_choice']}"
        
        # Prepare item for DynamoDB
        item = {
            'city_scenario': city_scenario,
            'outcome_stat_facet': outcome_stat_facet,
            'outcome': plot_info['outcome'],
            'statistic_type': plot_info['statistic_type'],
            'facet_choice': plot_info['facet_choice'],
            's3_key': plot_info['s3_key'],
            'file_size': plot_info['file_size'],
            'created_at': plot_info['created_at']
        }
        
        try:
            # Insert item into DynamoDB
            table.put_item(Item=item)
            print(f"✅ Registered: {plot_info['outcome']} ({plot_info['s3_key']})")
            
        except Exception as e:
            print(f"❌ Error registering {plot_info['outcome']}: {str(e)}")
    
    print("\n🎯 Registration complete!")
    
    # Verify the data was inserted
    print("\n📊 Verifying data...")
    try:
        response = table.scan()
        items = response['Items']
        print(f"✅ Found {len(items)} plots in database")
        
        for item in items:
            print(f"   - {item['outcome']} -> {item['s3_key']}")
            
    except Exception as e:
        print(f"❌ Error verifying data: {str(e)}")

if __name__ == "__main__":
    register_existing_plots()
