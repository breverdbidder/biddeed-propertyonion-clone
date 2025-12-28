#!/usr/bin/env python3
"""
Brevard County Foreclosure Scraper
Scrapes official public sources and populates Supabase
"""

import os
import requests
import json
from datetime import datetime

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

def scrape_brevard_clerk():
    """Scrape official Brevard Clerk foreclosure list"""
    print("📋 Scraping Brevard Clerk foreclosure list...")
    
    url = "http://vweb2.brevardclerk.us/Foreclosures/foreclosure_sales.html"
    response = requests.get(url)
    
    # Parse HTML table for case numbers, names, dates
    cases = []
    lines = response.text.split('\n')
    
    for line in lines:
        if 'FC-' in line or 'CA-' in line:
            # Extract case number, plaintiff, defendant
            # Format: | case_number | plaintiff VS defendant | comment | date |
            parts = line.split('|')
            if len(parts) >= 4:
                case = {
                    'case_number': parts[1].strip(),
                    'parties': parts[2].strip(),
                    'auction_date': parts[4].strip() if len(parts) > 4 else ''
                }
                
                # Split plaintiff VS defendant
                if ' VS ' in case['parties']:
                    plaintiff, defendant = case['parties'].split(' VS ', 1)
                    case['plaintiff'] = plaintiff.strip()
                    case['defendant'] = defendant.strip()
                    cases.append(case)
    
    print(f"✅ Found {len(cases)} cases")
    return cases

def lookup_bcpao(owner_name):
    """Look up property in BCPAO by owner name"""
    try:
        # BCPAO API search by owner
        url = f"https://www.bcpao.us/api/v1/search?q={owner_name}&type=owner"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                prop = data['results'][0]
                return {
                    'parcel_id': prop.get('parcel_id'),
                    'address': prop.get('property_address'),
                    'city': prop.get('city'),
                    'assessed_value': prop.get('assessed_value'),
                    'photo_url': f"https://www.bcpao.us/photos/{prop.get('parcel_id', '')[:2]}/{prop.get('parcel_id', '')}011.jpg"
                }
    except:
        pass
    
    return {}

def insert_to_supabase(properties):
    """Insert properties into Supabase"""
    print(f"💾 Inserting {len(properties)} properties into Supabase...")
    
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    url = f"{SUPABASE_URL}/rest/v1/properties"
    
    response = requests.post(url, headers=headers, json=properties)
    
    if response.status_code in [200, 201]:
        print(f"✅ Inserted successfully")
        return True
    else:
        print(f"❌ Insert failed: {response.status_code}")
        print(response.text[:200])
        return False

def main():
    print("🚀 Starting Brevard County foreclosure scrape...")
    print(f"Time: {datetime.now()}")
    
    # Scrape Brevard Clerk
    cases = scrape_brevard_clerk()
    
    # Enrich with BCPAO data
    properties = []
    for case in cases[:10]:  # Start with first 10
        print(f"Looking up: {case.get('defendant', 'Unknown')}")
        
        bcpao_data = lookup_bcpao(case.get('defendant', ''))
        
        prop = {
            'case_number': case.get('case_number'),
            'plaintiff': case.get('plaintiff'),
            'owner_name': case.get('defendant'),
            'auction_date': case.get('auction_date'),
            'data_source': 'brevard_clerk',
            'county': 'Brevard',
            **bcpao_data
        }
        
        if prop.get('address'):
            properties.append(prop)
            print(f"  ✅ {prop['address']}")
        else:
            print(f"  ⚠️  No address found")
    
    # Insert to Supabase
    if properties:
        insert_to_supabase(properties)
    
    print(f"\n✅ Scrape complete: {len(properties)} properties added")

if __name__ == '__main__':
    main()
