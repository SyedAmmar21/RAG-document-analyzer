import modal


APP_NAME = "sandbox-learning"
FUNCTION_NAME = "analyze_file"


def run_sandbox(payload):
    """
    Call deployed Modal sandbox function.
    """

    sandbox_function = modal.Function.lookup(
        APP_NAME,
        FUNCTION_NAME,
    )

    return sandbox_function.remote(payload)