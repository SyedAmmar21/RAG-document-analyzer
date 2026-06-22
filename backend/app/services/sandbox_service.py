import modal


def run_sandbox(payload):
    """
    Generic sandbox gateway.

    Payload example:

    {
        "action": "export_document",
        "document_type": "pptx",
        "content": {
            "title": "...",
            "slides": [...]
        }
    }

    Legacy payloads such as `create_presentation` are still accepted by the
    sandbox dispatcher for backwards compatibility during the migration.
    """

    sandbox_function = modal.Function.from_name(
        "sandbox-learning",
        "analyze_file"
    )

    try:
        return sandbox_function.remote(payload)
    except Exception as exc:
        error_message = str(exc)

        # Local development can easily drift from the deployed Modal function.
        # If the remote sandbox has not been redeployed with the new generic
        # export action yet, fall back to the shared local implementation so
        # the backend API remains usable during refactors.
        if "Unknown action: export_document" not in error_message:
            raise

        from modal_sandbox.sandbox import process_payload

        return process_payload(payload)
