#!/usr/bin/env python3
import requests
import re
import json
from datetime import datetime

def scrape_brevard_clerk():
    print("📋 Scraping Brevard Clerk...")
    response = requests.get('http://vweb2.brevardclerk.us/Foreclosures/foreclosure_sales.html', timeout=30)
    html = response.text
    properties = []
    rows = re.findall(r'<tr>.*?</tr>', html, re.DOTALL)
    
    for row in rows:
        case_match = re.search(r'(\d{2}-\d{4}-[A-Z]{2}-\d{6}[^<]*)', row)
        if not case_match:
            continue
        
        case_number = case_match.group(1).strip()
        title_match = re.search(r'<td[^>]*>([^<]+VS[^<]+)</td>', row, re.I)
        
        if title_match:
            title = title_match.group(1).strip()
            parts = title.split(' VS ')
            plaintiff = parts[0].strip()[:100] if len(parts) > 0 else ''
            defendant = parts[1].strip()[:100] if len(parts) > 1 else ''
        else:
            plaintiff, defendant = '', ''
        
        date_match = re.search(r'(\d{2}-\d{2}-\d{4})', row)
        auction_date = date_match.group(1) if date_match else ''
        
        if auction_date and '-' in auction_date:
            parts = auction_date.split('-')
            if len(parts) == 3:
                auction_date = f'{parts[2]}-{parts[0]}-{parts[1]}'
        
        properties.append({
            'case_number': case_number,
            'plaintiff': plaintiff or 'Unknown',
            'defendant': defendant or 'Unknown',
            'auction_date': auction_date or 'TBD',
            'auction_type': 'Foreclosure',
            'status': 'Scheduled'
        })
    
    return properties

properties = scrape_brevard_clerk()
print(f"✅ Scraped {len(properties)} properties")

# Save to JSON
with open('/tmp/brevard_properties.json', 'w') as f:
    json.dump(properties, f, indent=2)

print(f"💾 Saved to /tmp/brevard_properties.json")

# Show first 3
print(f"\n📊 Sample properties:")
for p in properties[:3]:
    print(f"  {p['case_number']}: {p['plaintiff']} VS {p['defendant']} - {p['auction_date']}")

print(f"\n✅ Total: {len(properties)} real Brevard foreclosures")
