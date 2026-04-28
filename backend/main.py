import logging
import os
try:
    from agent_server import create_app
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server import create_app


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
)

preset = os.getenv("AGENT_SERVER_PRESET", "full_stack")
app = create_app(preset=preset)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
