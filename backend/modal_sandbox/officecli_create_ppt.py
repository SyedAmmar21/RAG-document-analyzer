import modal

app = modal.App("officecli-create-ppt")

image = (
    modal.Image.debian_slim()
    .apt_install(
        "curl",
        "libicu-dev"
    )
    .run_commands(
        "curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh -o install.sh",
        "bash install.sh"
    )
)


@app.function(image=image)
def create_ppt():

    import subprocess
    import tempfile

    import tempfile
    import os

    ppt_path = os.path.join(
        tempfile.gettempdir(),
        "test.pptx"
    )

    result = subprocess.run(
        [
            "/root/.local/bin/officecli",
            "new",
            ppt_path
        ],
        capture_output=True,
        text=True
    )

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


@app.local_entrypoint()
def main():

    result = create_ppt.remote()

    print(result)