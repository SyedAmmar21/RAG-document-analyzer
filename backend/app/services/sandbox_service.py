from modal_sandbox.sandbox import analyze_file


def run_sandbox(file_bytes: bytes):
    return analyze_file.remote(file_bytes)