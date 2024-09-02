from flask import Flask, request
from markupsafe import escape

from . import cli, util

__author__ = "Alex Noerdemann"
__license__ = "GNU GPL v3"
__version__ = "0.0.0"
__maintainer__ = "Alex Noerdemann"
__status__ = "Development"


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    cli.init(app)

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            user_input = escape(request.form["match-url"])
            util.parse_match(user_input)
            # TODO [HMP-TASK-?] Let frontend handle the parsed data.
            return "POST Done!"
        else:
            return ('<h1>Hello, HMP!</h1>'
                '<form method="POST"><input name="match-url"><input type="submit"></form>'
                )    

    return app
