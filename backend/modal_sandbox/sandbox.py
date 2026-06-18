import os
import modal
from openai import OpenAI


app = modal.App("sandbox-learning")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "openai",
        "reportlab"
    )
)

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("openai-secret")
    ]
)
def analyze_file(payload):

    action = payload.get("action")

    if action == "test":
        return {
            "status": "sandbox_alive"
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