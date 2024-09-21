import importlib.util
import subprocess
from pathlib import Path

from scrape.scrape.spiders import match


def get_module_parent_path(module_name : str):
    spec = importlib.util.find_spec(module_name)
    return Path(spec.origin).parent

def parse_match(url : str):
    scrape_path = get_module_parent_path("scrape.scrape")
    # TODO[HMP-TASK-4]: Adapt subprocess call to return file path
    process = subprocess.Popen(
        ["scrapy", "crawl", match.MatchSpider.name, f"-a start_urls={url}".replace(" ", "")],
        cwd=scrape_path,
    )
    process.wait()
