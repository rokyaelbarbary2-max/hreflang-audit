#!/usr/bin/env python3
"""hreflang_audit.py - check the hreflang cluster of a page.

usage: python3 hreflang_audit.py https://example.com/en/pricing

For the start page and every alternate it declares, the script checks that:
  1. the URL answers 200 without a redirect,
  2. the page is not noindex,
  3. the canonical points at itself,
  4. the page lists every other member of the cluster (return links),
  5. every hreflang value is a valid language(-REGION) code or x-default.
Exit code 0 = clean cluster, 1 = problems found.
"""
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (hreflang-audit)"
CODE = re.compile(r"^(x-default|[a-z]{2,3}(-[A-Z]{2}|-[0-9]{3})?)$")


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.alternates, self.canonical, self.robots = {}, None, ""

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        rel = a.get("rel", "").lower().split()
        if tag == "link" and "alternate" in rel and a.get("hreflang"):
            self.alternates[a["hreflang"]] = a.get("href", "")
        elif tag == "link" and "canonical" in rel:
            self.canonical = a.get("href", "")
        elif tag == "meta" and a.get("name", "").lower() == "robots":
            self.robots += " " + a.get("content", "").lower()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with OPENER.open(req, timeout=20) as r:
            status, body, xrobots = r.status, r.read(500_000).decode("utf-8", "ignore"), r.headers.get("X-Robots-Tag", "")
    except urllib.error.HTTPError as e:
        status, body, xrobots = e.code, "", e.headers.get("X-Robots-Tag", "")
    p = HeadParser()
    p.feed(body)
    return status, p, xrobots.lower()


def norm(u):
    return u.split("#")[0].rstrip("/")


def main():
    start = sys.argv[1]
    status, page, _ = fetch(start)
    if status != 200:
        print(f"start page answered {status}; fix that first")
        sys.exit(1)
    cluster = dict(page.alternates)
    if not cluster:
        print("no hreflang annotations found on the start page")
        sys.exit(1)
    problems = []
    for code in cluster:
        if not CODE.match(code):
            problems.append(f"invalid hreflang value '{code}'")
    urls = {norm(u) for u in cluster.values()}
    if norm(start) not in urls:
        problems.append("start page does not reference itself in its own cluster")
    for code, url in sorted(cluster.items()):
        st, p, xr = fetch(url)
        tag = f"[{code}] {url}"
        if st != 200:
            problems.append(f"{tag}: HTTP {st} (alternates must answer 200 directly)")
            continue
        if "noindex" in p.robots or "noindex" in xr:
            problems.append(f"{tag}: noindex")
        if p.canonical and norm(p.canonical) != norm(url):
            problems.append(f"{tag}: canonical points to {p.canonical}")
        missing = urls - {norm(u) for u in p.alternates.values()}
        if missing:
            problems.append(f"{tag}: missing return links to {sorted(missing)}")
        print(f"checked {tag}: {st}, {len(p.alternates)} annotations")
    if problems:
        print("\nPROBLEMS")
        for pr in problems:
            print(" -", pr)
        sys.exit(1)
    print("\ncluster is consistent")


if __name__ == "__main__":
    main()
