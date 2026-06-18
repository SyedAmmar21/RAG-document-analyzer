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
        "bash install.sh",

        # diagnostics
        "which officecli || true",
        "officecli --version || true",
        "dotnet --info || true",
        "ls -R /root/.local || true"
    )
)

OFFICECLI = "/root/.local/bin/officecli"


@app.function(image=image)
def create_ppt(title: str, slides: list[str]):

    import subprocess

    ppt_path = "/tmp/test.pptx"

    create_result = subprocess.run(
        [
            OFFICECLI,
            "create",
            ppt_path
        ],
        capture_output=True,
        text=True
    )

    if create_result.returncode != 0:
        raise Exception(create_result.stderr)

    slide_result = subprocess.run(
        [
            OFFICECLI,
            "add",
            ppt_path,
            "/",
            "--type",
            "slide"
        ],
        capture_output=True,
        text=True
    )

    if slide_result.returncode != 0:
        raise Exception(slide_result.stderr)

    textbox_result = subprocess.run(
        [
            OFFICECLI,
            "add",
            ppt_path,
            "/slide[1]",
            "--type",
            "textbox",
            "--prop",
            f"text={title}"
        ],
        capture_output=True,
        text=True
    )

    save_result = subprocess.run(
        [
            OFFICECLI,
            "save",
            ppt_path
        ],
        capture_output=True,
        text=True
    )

    if save_result.returncode != 0:
        raise Exception(save_result.stderr)

    with open(ppt_path, "rb") as f:
        return f.read()

@app.local_entrypoint()
def main():

    from pathlib import Path

    ppt_bytes = create_ppt.remote(
        "Demo Presentation",
        [
            "Introduction",
            "Results",
            "Conclusion"
        ]
    )

    output_dir = Path("sandbox_outputs")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "officecli_demo.pptx"

    with open(output_file, "wb") as f:
        f.write(ppt_bytes)

    print(f"Saved to: {output_file.resolve()}")