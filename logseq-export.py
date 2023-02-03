import marko
from marko.inline import InlineElement
from marko.block import BlockElement, Element
import marko.inline
from re import Match
import sys
import os


class BlockRef(InlineElement):
    pattern = r"^\(\(([^)]+)\)\)$"
    parse_children = False
    id = None

    def __init__(self, match: Match) -> None:
        self.id = match.group(1)


class LogSeqExtension:
    elements = [BlockRef]


def render_html(file):
    content = open(file).read()
    return marko.convert(content)


def render(el: Element, depth=0):
    prefix = "  " * depth
    print(prefix, end='')
    if isinstance(el, marko.block.List):
        print("UL")
    elif isinstance(el, marko.block.ListItem):
        print("LI")
    elif isinstance(el, marko.block.Paragraph):
        print("P")
    elif isinstance(el, marko.block.Document):
        print("HTML")
    elif isinstance(el, marko.inline.LineBreak):
        print(prefix)
    elif isinstance(el, BlockRef):
        print(f"*{el.id}")
    elif isinstance(el, marko.inline.RawText):
        print(el.children)
    else:
        raise ValueError(f"Invalid element type: {type(el)}")
    if isinstance(el, BlockElement):
        for c in el.children:
            render(c, depth=depth + 1)


def migrate_logseq_files(logseq_path: str, output_path: str):
    for file in os.listdir(logseq_path):
        if file.endswith(".md"):
            title = file[:-3]
            from_path = logseq_path + "/" + file
            to_path = output_path + "/" + file
            html = render_html(from_path)
            html = f"---\ntitle: {title}\n---\n" + html
            open(to_path, 'w').write(html)


if __name__ == "__main__":
    # input = sys.argv[1]
    # output_path = "./content/notes"
    # migrate_logseq_files(input, output_path)

    file_path = sys.argv[1]
    content = open(file_path).read()
    md = marko.Markdown(extensions=[LogSeqExtension])
    ast = md.parse(content)
    print(f"{render(ast)}")
