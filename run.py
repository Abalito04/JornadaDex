import os

from app import create_app
from app.config import clean_env_value

app = create_app()


if __name__ == "__main__":
    debug = clean_env_value(os.getenv("FLASK_DEBUG", "false")).lower() == "true"
    app.run(debug=debug, use_reloader=debug)
