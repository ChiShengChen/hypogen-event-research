"""Convert issuer article content to stable, line-numbered blocks."""

import argparse
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup, NavigableString, Tag


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def rows(node):
    if not isinstance(node, Tag) or node.name in {"script", "style", "svg", "noscript", "button", "iframe"}:
        return
    if node.name == "table" and not node.find("table"):
        for row in node.find_all("tr"):
            cells = [clean(cell.get_text(" ", strip=True)) for cell in row.find_all(("th", "td"), recursive=False)]
            if any(cells):
                yield " | ".join(cells).strip(" |")
        return
    if node.name in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre"} and not node.find(["table", "ul", "ol"]):
        if line := clean(node.get_text(" ", strip=True)):
            yield line
        return
    inline = []
    for child in node.children:
        if isinstance(child, NavigableString):
            if clean(str(child)):
                inline.append(clean(str(child)))
        elif child.name in {"span", "a", "em", "b", "strong", "i", "sup", "sub"} and not child.find(["div", "p", "table", "ul", "ol"]):
            inline.append(clean(child.get_text(" ", strip=True)))
        else:
            if any(inline):
                yield " ".join(inline)
            inline = []
            yield from rows(child)
    if any(inline):
        yield " ".join(inline)


def extract(source, selector, omit=None):
    soup = BeautifulSoup(source.read_bytes(), "html.parser")
    article = soup.select_one(selector)
    if article is None:
        raise ValueError(f"Article selector missing in {source}: {selector}")
    if omit:
        for node in article.select(omit):
            node.decompose()
    lines = list(rows(article))
    return [{"page": index // 45 + 1, "row": index % 45 + 1, "text": line}
            for index, line in enumerate(lines)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("selector")
    parser.add_argument("--omit")
    args = parser.parse_args()
    print(json.dumps(extract(args.source, args.selector, args.omit), ensure_ascii=False))
