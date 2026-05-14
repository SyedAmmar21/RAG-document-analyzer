"""Test the /domains endpoint directly via HTTP"""
import requests
import json

# Assuming backend is running on localhost:8000
BASE_URL = "http://localhost:8000"

try:
    response = requests.get(f"{BASE_URL}/domains")
    
    if response.status_code == 200:
        domains = response.json().get("domains", [])
        print(f"✓ API returned {len(domains)} folders\n")
        
        # Show all folders
        print("Folders:")
        for d in domains:
            print(f"  • {d['name']} (ID: {d['id']}) - {d['document_count']} documents")
        
        # Check for Unorganized Files
        unorganized = [d for d in domains if d.get("id") == "unorganized"]
        if unorganized:
            print(f"\n✓ SUCCESS: 'Unorganized Files' IS showing in folder list!")
            print(f"  Document count: {unorganized[0]['document_count']}")
        else:
            print(f"\n✗ Issue: 'Unorganized Files' NOT in folder list")
    else:
        print(f"Error: API returned status {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect to backend at http://localhost:8000")
    print("  Make sure the backend server is running")
