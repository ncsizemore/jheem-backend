#!/usr/bin/env python3
"""
Script to test the discovery API and verify everything is working
"""

import requests
import json

def test_discovery_api():
    """Test the discovery API endpoints"""
    
    # Assuming your API Gateway ID is still qn20ihefoo
    # You might need to update this if it changed
    base_url = "http://localhost:4566/restapis/qn20ihefoo/local/_user_request_"
    
    print("🧪 Testing JHEEM Discovery API")
    print("=" * 50)
    
    # Test 1: Search for plots
    print("\n1️⃣ Testing plot discovery...")
    search_url = f"{base_url}/plots/search?city=C.12580&scenario=cessation"
    
    try:
        response = requests.get(search_url)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data.get('total_plots', 0)} plots")
            for plot in data.get('plots', []):
                print(f"      - {plot['outcome']} -> {plot['s3_key']}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Connection error: {str(e)}")
    
    # Test 2: Search with outcome filter
    print("\n2️⃣ Testing filtered discovery...")
    filter_url = f"{base_url}/plots/search?city=C.12580&scenario=cessation&outcomes=incidence,diagnosed.prevalence"
    
    try:
        response = requests.get(filter_url)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data.get('total_plots', 0)} filtered plots")
            for plot in data.get('plots', []):
                print(f"      - {plot['outcome']} -> {plot['s3_key']}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Connection error: {str(e)}")
    
    # Test 3: Fetch an actual plot
    print("\n3️⃣ Testing plot retrieval...")
    plot_url = f"{base_url}/plot?plotKey=plots/jheem_real_plot.json"
    
    try:
        response = requests.get(plot_url)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Successfully retrieved plot data")
            print(f"      - Data arrays: {len(data.get('data', []))}")
            print(f"      - Layout keys: {list(data.get('layout', {}).keys())[:5]}...")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Connection error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Test complete!")

if __name__ == "__main__":
    test_discovery_api()
