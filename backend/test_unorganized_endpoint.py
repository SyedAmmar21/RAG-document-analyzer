"""Test the /domains endpoint to verify Unorganized Files appears"""
from app.services.domain_service import get_all_domains
import json

domains = get_all_domains()

print("Domains returned from get_all_domains():")
print(json.dumps(domains, indent=2))

# Check if Unorganized Files is included
unorganized = [d for d in domains if d.get("id") == "unorganized"]
if unorganized:
    print(f"\n✓ SUCCESS: 'Unorganized Files' is in the list!")
    print(f"  Name: {unorganized[0]['name']}")
    print(f"  Document count: {unorganized[0]['document_count']}")
else:
    print("\n✗ ERROR: 'Unorganized Files' NOT found in domains list")
