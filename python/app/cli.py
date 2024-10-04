import click

from . import util


def init(app):
    @app.cli.command("parse-match")
    @click.argument("match_url", nargs=1)
    @click.argument("output_path", nargs=1)
    def parse_match(match_url, output_path):
        util.parse_match(match_url, output_path)
