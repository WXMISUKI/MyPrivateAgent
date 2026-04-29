import os
try:
    from agent_server import create_app
except ModuleNotFoundError:
    from backend.agent_server import create_app

try:
    from logging_config import setup_logging
except ModuleNotFoundError:
    from backend.logging_config import setup_logging

setup_logging()

preset = os.getenv("AGENT_SERVER_PRESET", "full_stack")
app = create_app(preset=preset)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
