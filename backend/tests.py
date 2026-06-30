from app.services.sandbox.session_store import get_backend

THREAD_ID = "the_same_thread_id_you_used"

backend = get_backend(THREAD_ID)

result = backend.execute("ls -lah /workspace/output")

print(result.exit_code)
print(result.output)