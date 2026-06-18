import modal

app = modal.App("sandbox-learning")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "openai",
        "reportlab"
    )
)

@app.function(image=image)
def analyze_file(payload):

    action = payload.get("action")

    # ----------------------------------
    # TEST
    # ----------------------------------

    if action == "test":
        return {
            "status": "sandbox_alive"
        }

    # ----------------------------------
    # CREATE PRESENTATION
    # ----------------------------------

    if action == "create_presentation":

        title = payload["title"]
        slides = payload["slides"]

        ppt_function = modal.Function.from_name(
            "officecli-create-ppt",
            "create_ppt"
        )

        ppt_bytes = ppt_function.remote(
            title,
            slides
        )

        return {
            "status": "success",
            "file_bytes": ppt_bytes
        }

    raise ValueError(
        f"Unknown action: {action}"
    )


@app.local_entrypoint()
def main():

    result = analyze_file.remote(
        {
            "action": "test"
        }
    )

    print(result)