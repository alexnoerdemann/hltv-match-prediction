import click

from . import util


def init(app):
    @app.cli.command("parse-match")
    @click.argument("match_url")
    def parse_match(match_url):
        util.parse_match(match_url)
