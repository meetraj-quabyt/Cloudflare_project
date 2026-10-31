import os
import sys

# Ensure app package importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from workers import WorkerEntrypoint

from app.main import create_app


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi

        env = self.env
        app = create_app(env=env)
        return await asgi.fetch(app, request.js_object, env)