#!/usr/bin/env python3
"""
Together AI Dedicated Containers — Sprocket Hello World App

A minimal Sprocket worker template. Deploy with `together beta jig deploy`.

This file is the application entrypoint (app.py). Pair it with a
pyproject.toml configuration (see example below).

Usage:
    # Local test (requires sprocket installed)
    python sprocket_hello_world.py

    # Deploy to Together
    together beta jig deploy

Requires:
    pip install sprocket --extra-index-url https://pypi.together.ai/
    # For deployment: uv pip install "together>=2.0.0"

Example pyproject.toml:
    [project]
    name = "my-sprocket-app"
    version = "0.1.0"

    [tool.jig.image]
    python_version = "3.11"
    system_packages = []
    cmd = "python app.py --queue"
    copy = ["app.py"]

    [tool.jig.deploy]
    gpu_type = "h100-80gb"
    gpu_count = 1
    min_replicas = 1
    max_replicas = 5
    port = 8000
    health_check_path = "/health"
"""

import sprocket


class HelloModel(sprocket.Sprocket):
    """Minimal Sprocket worker — echo input with transformation."""

    def setup(self) -> None:
        """Called once at startup. Load models, weights, or resources here."""
        # Example: self.model = load_my_model("weights/")
        print("Model loaded and ready.")

    def predict(self, args: dict) -> dict:
        """Called for each job. Process input and return output.

        Args:
            args: Job payload dict (from queue submission or HTTP request).

        Returns:
            dict: Response payload sent back to the caller.
        """
        text = args.get("text", "")
        operation = args.get("operation", "upper")

        if operation == "upper":
            result = text.upper()
        elif operation == "reverse":
            result = text[::-1]
        elif operation == "word_count":
            result = str(len(text.split()))
        else:
            result = text

        return {
            "input": text,
            "operation": operation,
            "result": result,
        }

    def shutdown(self) -> None:
        """Called on graceful shutdown. Optional cleanup."""
        print("Shutting down.")


if __name__ == "__main__":
    sprocket.run(HelloModel(), "my-org/hello-model")
