from app.services.domain_centroid_service import (
    recompute_domain_centroid,
)

domain_id = 2

centroid = recompute_domain_centroid(domain_id)

if centroid:
    print("Domain centroid updated")
    print("Length:", len(centroid))
    print("First 5 values:", centroid[:5])
else:
    print("No centroid generated")