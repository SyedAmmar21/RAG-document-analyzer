from app.services.sandbox.session_store import (
    get_backend,
    set_current_document,
    get_current_document,
    WorkingDocument,
)

THREAD_ID = "memory-test"

# Create a sandbox session
get_backend(THREAD_ID)

# Store a document
set_current_document(
    THREAD_ID,
    WorkingDocument(
        filename="gold.pptx",
        path="/workspace/output/gold.pptx",
        file_type="pptx",
    ),
)

# Read it back
document = get_current_document(THREAD_ID)

print(document)
print(document.filename)
print(document.path)
print(document.file_type)
print(get_current_document("another-thread"))