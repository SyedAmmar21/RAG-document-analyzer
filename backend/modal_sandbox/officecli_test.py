import modal

app = modal.App("officecli-test")

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
def officecli_version():

    import subprocess

    result = subprocess.run(
        ["/root/.local/bin/officecli", "--help"],
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

    result = officecli_version.remote()

    print(result)