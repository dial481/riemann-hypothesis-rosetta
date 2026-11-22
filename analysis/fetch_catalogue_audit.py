"""Cache checksum-pinned audit snapshots, respecting robots.txt and a shared rate limit."""
import argparse
import hashlib
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from catalogue_links import GRAPH_SHA, PAGE_HASHES
from odesky_coverage import HTML_SHA, URL

AGENT = "Rosetta-catalogue-audit"


def fetch(directory):
    resources = {"index.html": HTML_SHA, "graph.html": GRAPH_SHA,
                 **{f"s/{slug}.html":sha for slug,sha in PAGE_HASHES.items()}}
    missing = []
    for name, sha in resources.items():
        file = directory/name
        if file.exists():
            if hashlib.sha256(file.read_bytes()).hexdigest() != sha:
                raise ValueError(f"Cached checksum mismatch for {name}")
        else:
            missing.append(name)
    if not missing:
        return
    def get(url):
        request = Request(url,headers={"User-Agent": AGENT})
        with urlopen(request,timeout=90) as stream:
            return stream.read()
    robots = RobotFileParser()
    try:
        rules = get(urljoin(URL,"/robots.txt")).decode()
    except HTTPError as error:
        if error.code not in {404,410}:
            raise
        rules = ""
    robots.parse(rules.splitlines())
    rate = robots.request_rate(AGENT)
    delay = max(1.05, robots.crawl_delay(AGENT) or 0, rate.seconds/rate.requests if rate else 0)
    for name in missing:
        url = urljoin(URL,name)
        if not robots.can_fetch(AGENT,url):
            raise ValueError(f"robots.txt disallows {url}")
        time.sleep(delay)
        data = get(url)
        if hashlib.sha256(data).hexdigest() != resources[name]:
            raise ValueError(f"Snapshot changed for {url}. Use the frozen identifier indexes.")
        file = directory/name
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes(data)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    fetch(cli.parse_args().directory)
