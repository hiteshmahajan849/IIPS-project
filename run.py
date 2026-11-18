"""Entrypoint: `python run.py` or `flask --app run.py run`."""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
