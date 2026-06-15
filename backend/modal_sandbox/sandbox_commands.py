import modal

app = modal.App("sandbox-commands")

image = (
    modal.Image.debian_slim()
    .apt_install("zip")
)


@app.function(image=image)
def run_command():

    import subprocess

    result = subprocess.run(
        ["python", "--version"],
        capture_output=True,
        text=True
    )

    return result.stdout

@app.function(image=image)
def inspect_file():

    import os

    file_path = "/tmp/test.txt"

    with open(file_path, "w") as f:
        f.write("Hello from Modal Sandbox")

    size = os.path.getsize(file_path)

    return {
        "exists": os.path.exists(file_path),
        "size": size
    }

@app.function(image=image)
def modify_with_command():

    import subprocess

    input_file = "/tmp/input.txt"

    with open(input_file, "w") as f:
        f.write("hello modal")

    subprocess.run(
        [
            "sed",
            "-i",
            "s/hello/HELLO/g",
            input_file
        ],
        check=True
    )

    with open(input_file, "r") as f:
        return f.read()
    
@app.function(image=image)
def create_zip(file_bytes):

    import tempfile
    import subprocess

    with tempfile.TemporaryDirectory() as temp_dir:

        input_path = f"{temp_dir}/note.txt"

        with open(input_path, "wb") as f:
            f.write(file_bytes)

        zip_path = f"{temp_dir}/output.zip"

        subprocess.run(
            [
                "zip",
                "-j",
                zip_path,
                input_path
            ],
            check=True
        )

        with open(zip_path, "rb") as f:
            return f.read()
    
@app.local_entrypoint()
def main():

    with open(
        r"C:\Users\USER\Downloads\note.txt",
        "rb"
    ) as f:
        file_bytes = f.read()

    zip_bytes = create_zip.remote(
        file_bytes
    )

    with open(
        r"C:\Users\USER\Downloads\note.zip",
        "wb"
    ) as f:
        f.write(zip_bytes)

    print("ZIP created.")