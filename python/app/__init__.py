from flask import Flask

__author__ = "Alex Noerdemann"
__license__ = "GNU GPL v3"
__version__ = "0.0.0"
__maintainer__ = "Alex Noerdemann"
__status__ = "Development"


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "Hello, HMP!"

    return app
