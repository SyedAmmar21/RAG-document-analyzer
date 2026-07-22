import inspect

from app.services.sandbox.cube.cube_sandbox_service import CubeSandboxService
from app.services.sandbox.cube.cube_sandbox_initializer import CubeSandboxInitializer

print("=" * 80)
print("Create Sandbox")
print("=" * 80)

service = CubeSandboxService()
sandbox = service.create_sandbox()

initializer = CubeSandboxInitializer(sandbox)
initializer.initialize()

print("=" * 80)
print("FILES API")
print("=" * 80)
print(dir(sandbox.files))

print("=" * 80)
print("SANDBOX API")
print("=" * 80)
print(dir(sandbox))

print("=" * 80)
print("Create test file")
print("=" * 80)

sandbox.commands.run(
    "mkdir -p /workspace/output && echo 'Hello from CubeSandbox' > /workspace/output/test.txt",
    user="root",
)

print("=" * 80)
print("List output directory")
print("=" * 80)

result = sandbox.commands.run(
    "ls -lah /workspace/output",
    user="root",
)

print(result.stdout)

print("=" * 80)
print("Read() signature")
print("=" * 80)

print(inspect.signature(sandbox.files.read))

print("=" * 80)
print("Read() docstring")
print("=" * 80)

print(inspect.getdoc(sandbox.files.read))

print("=" * 80)
print("Test 1 - format=text gzip=False")
print("=" * 80)

try:
    content = sandbox.files.read(
        "/workspace/output/test.txt",
        format="text",
        gzip=False,
    )
    print(repr(content))
except Exception as e:
    print(type(e).__name__)
    print(e)

print("=" * 80)
print("Test 2 - format=bytes gzip=False")
print("=" * 80)

try:
    content = sandbox.files.read(
        "/workspace/output/test.txt",
        format="bytes",
        gzip=False,
    )
    print(content)
except Exception as e:
    print(type(e).__name__)
    print(e)

print("=" * 80)
print("Test 3 - format=stream gzip=False")
print("=" * 80)

try:
    stream = sandbox.files.read(
        "/workspace/output/test.txt",
        format="stream",
        gzip=False,
    )
    print(stream)
except Exception as e:
    print(type(e).__name__)
    print(e)

print("=" * 80)
print("Test 4 - format=text gzip=True")
print("=" * 80)

try:
    content = sandbox.files.read(
        "/workspace/output/test.txt",
        format="text",
        gzip=True,
    )
    print(repr(content))
except Exception as e:
    print(type(e).__name__)
    print(e)

print("=" * 80)
print("Test 5 - format=text user=root")
print("=" * 80)

try:
    content = sandbox.files.read(
        "/workspace/output/test.txt",
        format="text",
        user="root",
        gzip=False,
    )
    print(repr(content))
except Exception as e:
    print(type(e).__name__)
    print(e)

print("=" * 80)
print("Underlying envd client")
print("=" * 80)

print(type(sandbox.files._envd_api))
print(dir(sandbox.files._envd_api))
from e2b.sandbox_sync.filesystem.filesystem import ENVD_API_FILES_ROUTE

print("=" * 80)
print("Filesystem route")
print("=" * 80)

print("Route:", ENVD_API_FILES_ROUTE)
print("Base URL:", sandbox.files._envd_api.base_url)
print("Default headers:", sandbox.files._envd_api.headers)
print("=" * 80)
print("Raw request object")
print("=" * 80)

request = sandbox.files._envd_api.build_request(
    "GET",
    ENVD_API_FILES_ROUTE,
    params={"path": "/workspace/output/test.txt"},
)

print("URL:", request.url)
print("Headers:", request.headers)

print("=" * 80)
print("Raw HTTP request")
print("=" * 80)

client = sandbox.files._envd_api

try:
    response = client.get(
        "/files/read",
        params={
            "path": "/workspace/output/test.txt",
        },
    )

    print("Status:", response.status_code)
    print()

    print("Headers:")
    print(response.headers)
    print()

    print("First 200 bytes:")
    print(response.content[:200])

except Exception as e:
    print(type(e).__name__)
    print(e)

print("=" * 80)
print("Done")
print("=" * 80)

print("=" * 80)
print("DOWNLOAD URL TEST")
print("=" * 80)

print()

url = sandbox.download_url("/workspace/output/test.txt")

print("Generated URL:")
print(url)

print()

import httpx

with httpx.Client(
    headers={"Accept-Encoding": "identity"}
) as client:

    response = client.get(url)

print("Status:", response.status_code)
print("Headers:")
print(response.headers)

print()

print("Raw bytes:")
print(response.content)

print("HTTP Status:", response.status_code)
print("Headers:", response.headers)

print()

print("Content:")
print(response.content)

try:
    print("download_url:", sandbox.download_url)
except Exception as e:
    print("download_url attribute failed:", e)

try:
    import inspect
    print("\nSignature:")
    print(inspect.signature(sandbox.download_url))
except Exception as e:
    print("signature failed:", e)

try:
    print("\nDoc:")
    print(inspect.getdoc(sandbox.download_url))
except Exception as e:
    print("doc failed:", e)