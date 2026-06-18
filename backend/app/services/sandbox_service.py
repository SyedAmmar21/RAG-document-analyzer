import modal


def run_sandbox(payload):
    """
    Generic sandbox gateway.

    Payload example:

    {
        "action": "create_presentation",
        "title": "...",
        "slides": [...]
    }
    """

    sandbox_function = modal.Function.from_name(
        "sandbox-learning",
        "analyze_file"
    )

    return sandbox_function.remote(payload)