import modal

app = modal.App("officecli-create-ppt")

image = (
    modal.Image.debian_slim()
    .apt_install("curl", "libicu-dev")
    .run_commands(
        "curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh -o install.sh",
        "bash install.sh"
    )
)

OFFICECLI = "/root/.local/bin/officecli"


@app.function(image=image)
def create_ppt(title: str, slides: list[str]):

    import subprocess

    ppt_path = "/tmp/test.pptx"

    # Create presentation
    subprocess.run(
        [
            OFFICECLI,
            "new",
            ppt_path,
            "--type",
            "pptx"
        ],
        check=True,
        capture_output=True,
        text=True
    )

    # ----------------------------
    # TITLE SLIDE
    # ----------------------------

    subprocess.run(
        [
            OFFICECLI,
            "add",
            ppt_path,
            "/",
            "--type",
            "slide"
        ],
        check=True,
        capture_output=True,
        text=True
    )

    subprocess.run(
        [
            OFFICECLI,
            "add",
            ppt_path,
            "/slide[1]",
            "--type",
            "textbox",
            "--prop",
            f"text={title}",
            "--prop",
            "x=1cm",
            "--prop",
            "y=1cm",
            "--prop",
            "width=20cm",
            "--prop",
            "height=5cm"
        ],
        check=True,
        capture_output=True,
        text=True
    )

    # ----------------------------
    # CONTENT SLIDES
    # ----------------------------

    for index, slide_title in enumerate(slides, start=2):

        subprocess.run(
            [
                OFFICECLI,
                "add",
                ppt_path,
                "/",
                "--type",
                "slide"
            ],
            check=True,
            capture_output=True,
            text=True
        )

        textbox_result = subprocess.run(
            [
                OFFICECLI,
                "add",
                ppt_path,
                f"/slide[{index}]",
                "--type",
                "textbox",
                "--prop",
                f"text={slide_title}",
                "--prop",
                "x=1cm",
                "--prop",
                "y=1cm",
                "--prop",
                "width=20cm",
                "--prop",
                "height=5cm"
            ],
            capture_output=True,
            text=True
        )

        print(textbox_result.stdout)

    # Save document
    save_result = subprocess.run(
        [
            OFFICECLI,
            "save",
            ppt_path
        ],
        capture_output=True,
        text=True
    )

    print(save_result.stdout)

    # Debug inspection
    inspect_result = subprocess.run(
        [
            OFFICECLI,
            "get",
            ppt_path,
            "/"
        ],
        capture_output=True,
        text=True
    )

    print(inspect_result.stdout)

    # Return ppt bytes
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