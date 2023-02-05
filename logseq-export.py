from pathlib import Path, PosixPath
from typing import Generator
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
    id: str

    def __init__(self, match: Match) -> None:
        self.id = match.group(1)


class WikiLink(InlineElement):
    pattern = r"\[\[([^]]+)\]\]"
    parse_children = False
    page: str

    def __init__(self, match: Match) -> None:
        self.page = match.group(1)


class BlockEmbed(BlockElement):
    def __init__(self, children: Element) -> None:
        self.children = [children]


class Attribute(InlineElement):
    pattern = r"(?:^|\n)([a-zA-Z]+)::\s*([a-zA-Z0-9_-]+)"
    parse_children = False
    name: str
    value: str

    def __init__(self, match: Match) -> None:
        self.name = match.group(1)
        self.value = match.group(2)


class RendererMixins:
    def render_block_ref(self, el: BlockRef):
        return f"REFERENCE: {el.id}"

    def render_attribute(self, el: Attribute):
        return ""

    def render_wiki_link(self, el: WikiLink):
        return f"<a href='#'>[[{el.page}]]</a>"

    def render_block_embed(self, el: BlockEmbed):
        return f"<p class='embed'>{self.render_children(el)}</p>"


class LogSeqExtension:
    elements = [BlockRef, Attribute, WikiLink]
    renderer_mixins = [RendererMixins]


def get_children(el: Element) -> list[Element]:
    if isinstance(el, BlockElement) and hasattr(el, 'children'):
        return el.children
    else:
        return []


def find_all_refs(el: Element) -> dict[str: Element]:
    """Returns dictionary of all found UUID refs in a given markdown tree (key - UUID, value - marko Node)"""
    children = get_children(el)

    refs = {}
    """
    First heuristic - target is BlockElement
        * Paragraph
            * Attr(id, _)
        * BlockElement
    """
    if len(children) >= 2:
        [p, target] = el.children[0:2]
        if isinstance(p, marko.block.Paragraph) and len(p.children) == 1 and isinstance(target, BlockElement):
            attr = p.children[0]
            if isinstance(attr, Attribute) and attr.name == 'id':
                refs[attr.value] = target

    """
    Second heuristic - target is paragraph
        * Paragraph
            * ...
            * Attr(id, _)
    """
    if isinstance(el, marko.block.Paragraph) and len(children) >= 2:
        attr = el.children[-1]
        if isinstance(attr, Attribute) and attr.name == 'id':
            refs[attr.value] = el

    for child in children:
        refs = refs | find_all_refs(child)

    return refs


def render_html(file):
    content = open(file).read()
    return marko.convert(content)


def render(el: Element, depth=0):
    prefix = "  " * depth
    print(prefix, end='')
    if isinstance(el, marko.block.List):
        print("ul>")
    elif isinstance(el, marko.block.ListItem):
        print("li>")
    elif isinstance(el, marko.block.Paragraph):
        print("p>")
    elif isinstance(el, marko.block.Document):
        print("section>")
    elif isinstance(el, marko.block.Quote):
        print("quote>")
    elif isinstance(el, marko.inline.Link):
        print("link>")
    elif isinstance(el, marko.inline.LineBreak):
        print(prefix)
    elif isinstance(el, marko.block.BlankLine):
        print(prefix)
    elif isinstance(el, BlockRef):
        print(f"*{el.id}")
    elif isinstance(el, marko.inline.RawText):
        print(el.children)
    elif isinstance(el, Attribute):
        print(f"attr> {el.name}={el.value}")
    else:
        raise ValueError(f"Invalid element type: {type(el)}")
    if isinstance(el, BlockElement) and not isinstance(el, marko.block.BlankLine):
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


def enumerate_logseq_pages(logseq_path: str) -> Generator[PosixPath, None, None]:
    for file in Path(logseq_path).glob("pages/*.md"):
        yield file


def embed_refs(el: Element, refs: dict[str, Element]):
    """
    Replaces all BlockRef's in a md-tree with referenced blocks
    """
    if isinstance(el, BlockElement) and hasattr(el, 'children'):
        for (idx, child) in enumerate(el.children):
            if isinstance(child, BlockRef):
                id = child.id
                if id in refs:
                    el.children[idx] = BlockEmbed(refs[id])
            else:
                embed_refs(child, refs)


if __name__ == "__main__":
    # input = sys.argv[1]
    # output_path = "./content/notes"
    # migrate_logseq_files(input, output_path)

    logseq_path = sys.argv[1]
    file_to_render_path = sys.argv[2]

    md = marko.Markdown(extensions=[LogSeqExtension])

    refs = {}

    for page in enumerate_logseq_pages(logseq_path):
        ast = md.parse(open(page).read())
        refs = refs | find_all_refs(ast)

    # for (ref, node) in refs.items():
    #     print(f"ref: {ref}")
    #     print(f"{md.render(node)}")
    #     print()

    ast = md.parse(open(file_to_render_path).read())
    embed_refs(ast, refs)
    print("---")
    print("unsafe: true")
    print(f"title: {file_to_render_path}")
    print("---")
    print(md.render(ast))
