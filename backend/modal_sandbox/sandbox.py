import modal

app = modal.App("sandbox-learning")


@app.function()
def analyze_file(file_bytes: bytes):

    text = file_bytes.decode("utf-8")

    lines = text.splitlines()

    findings = []

    if "RAM" in text:
        findings.append("RAM")

    if "CPU" in text:
        findings.append("CPU")

    if "Storage" in text:
        findings.append("Storage")

    if "GPU" in text:
        findings.append("GPU")

    report = f"""
Document Analysis

Total Characters: {len(text)}
Total Lines: {len(lines)}

Detected Specifications:
"""

    for item in findings:
        report += f"\n- {item}"

    return report


@app.local_entrypoint()
def main():

    with open(r"C:\\Users\\USER\\Downloads\\note.txt", "rb") as f:
        file_bytes = f.read()

    analysis = analyze_file.remote(file_bytes)

    print(analysis)