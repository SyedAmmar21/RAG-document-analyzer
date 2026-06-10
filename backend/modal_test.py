# modal_test.py

import modal

app = modal.App("rag-sandbox")

@app.function()
def hello():
    return "Sandbox works!"