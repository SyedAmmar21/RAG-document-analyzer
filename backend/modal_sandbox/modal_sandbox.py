# modal_sandbox/sandbox.py

import modal

app = modal.App("rag-sandbox")


@app.function()
def generate_report(title: str):
    filename = f"{title}.txt"

    with open(filename, "w") as f:
        f.write(f"Report: {title}")

    return {
        "status": "success",
        "filename": filename
    }


@app.local_entrypoint()
def main():
    result = generate_report.remote("gold_outlook")

    print(result)