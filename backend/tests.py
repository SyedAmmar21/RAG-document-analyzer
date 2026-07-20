from app.services.cube_sandbox_service import CubeSandboxService
from app.services.cube_sandbox_initializer import CubeSandboxInitializer

service = CubeSandboxService()

sandbox = service.create_sandbox()

initializer = CubeSandboxInitializer(sandbox)

initializer.initialize()

service.terminate_sandbox()