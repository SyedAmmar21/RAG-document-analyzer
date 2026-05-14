"""Diagnostic script to check document organization status"""
from app.db.database import get_connection
import os

conn = get_connection()
cursor = conn.cursor()

# Total documents
cursor.execute("SELECT COUNT(*) as total FROM documents")
total = cursor.fetchone()["total"]
print(f"✓ Total documents in database: {total}")

# Documents WITH domain assignments
cursor.execute("SELECT COUNT(DISTINCT document_id) as organized FROM document_domains")
organized = cursor.fetchone()["organized"]
print(f"✓ Documents WITH domain assignments: {organized}")

# Documents WITHOUT domain assignments (unorganized)
cursor.execute("""
SELECT COUNT(*) as unorganized FROM documents d
WHERE d.id NOT IN (
    SELECT DISTINCT document_id FROM document_domains
)
""")
unorganized = cursor.fetchone()["unorganized"]
print(f"✓ Documents WITHOUT domain assignments (unorganized): {unorganized}")

print(f"\n--- Breakdown ---")
print(f"Organized:   {organized}")
print(f"Unorganized: {unorganized}")
print(f"Total:       {total}")

# Show examples of unorganized documents
print(f"\n--- Sample Unorganized Documents ---")
cursor.execute("""
SELECT id, file_path, created_date FROM documents d
WHERE d.id NOT IN (
    SELECT DISTINCT document_id FROM document_domains
)
ORDER BY d.created_date DESC
LIMIT 10
""")
rows = cursor.fetchall()
for row in rows:
    print(f"  • {row['id']} | {os.path.basename(row['file_path'])} | {row['created_date']}")

conn.close()
