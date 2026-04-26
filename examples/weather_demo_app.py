"""Example entrypoint for a weather-focused reusable agent demo."""

try:
    from backend.agent_server import create_app
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from agent_server import create_app


app = create_app(preset="weather_demo")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
