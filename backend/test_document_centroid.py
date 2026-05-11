from app.services.document_centroid_service import get_document_centroid


document_id = "3efd4499-5499-4513-9de2-c4017e86431b"

centroid = get_document_centroid(document_id)

if centroid:
    print("Centroid length:", len(centroid))
    print("First 5 values:", centroid[:5])
else:
    print("No centroid found")