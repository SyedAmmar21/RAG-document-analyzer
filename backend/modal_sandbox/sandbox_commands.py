import modal

app = modal.App("sandbox-commands")

image = modal.Image.debian_slim()


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
    
@app.local_entrypoint()
def main():

    result = modify_with_command.remote()

    print(result)