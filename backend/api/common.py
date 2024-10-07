import importlib.util
import subprocess
from pathlib import Path

from scrape.scrape.spiders import match


def get_module_parent_path(module_name: str):
    spec = importlib.util.find_spec(module_name)
    return Path(spec.origin).parent


def parse_match(url: str, output_path: str):
    scrape_path = get_module_parent_path("scrape.scrape")
    process = subprocess.Popen(
        [
            "scrapy",
            "crawl",
            match.MatchSpider.name,
            "-a",
            f"start_urls={url}",
            "-O",
            f"{output_path}",
        ],
        cwd=scrape_path,
    )
    process.wait()
