import logging
try:
    from agent_server import create_app
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server import create_app


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
)

app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
