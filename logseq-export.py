import argparse
from pathlib import Path, PosixPath
import sys
from typing import IO, Generator
import marko
from marko.inline import InlineElement
from marko.block import BlockElement, Element
import marko.inline
from re import Match
import re
import os
from os.path import basename
from itertools import chain


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
    source_page_title: str

    def __init__(self, title, children: Element) -> None:
        self.children = [children]
        self.source_page_title = title


class Attribute(InlineElement):
    pattern = r"(?:^|\n)([a-zA-Z]+)::\s*(.+)"
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
        return f"<a href='{NOTES_URL}/{escape_slug(el.page)}'>[[{el.page}]]</a>"

    def render_block_embed(self, el: BlockEmbed):
        href = f"{NOTES_URL}/{escape_slug(el.source_page_title)}"
        link = f"<p class='quote-source'><a href='{href}'>{el.source_page_title}</a></p>"
        return f"<div class='quote'>{link}{self.render_children(el)}</div>"


class LogSeqExtension:
    elements = [BlockRef, Attribute, WikiLink]
    renderer_mixins = [RendererMixins]


def get_children(el: Element) -> list[Element]:
    if isinstance(el, BlockElement) and hasattr(el, 'children'):
        return el.children
    else:
        return []


def page_title_from_filename(filename: str) -> str:
    return re.sub(r"\.md$", '', basename(filename))


def read_all_refs(logseq_path: str) -> dict[str, (str, Element)]:
    """
    Read all pages in logseq folder and return dictionary of following form:
    ```
    UUID: ("Page title", Element),
    ...
    """
    all_refs = {}
    pages = enumerate_logseq_pages(logseq_path)
    dairies = enumerate_logseq_journal(logseq_path)
    for page in chain(pages, dairies):
        ast = md.parse(open(page).read())
        refs = read_refs_from_ast(ast)
        title = page_title_from_filename(page)
        refs = {id: (title, ref)
                for (id, ref) in refs.items()}
        all_refs = all_refs | refs
    return all_refs


def read_refs_from_ast(el: Element) -> dict[str: Element]:
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
        if isinstance(p, marko.block.Paragraph) and len(p.children) >= 1 and isinstance(target, BlockElement):
            is_attr = [isinstance(c, Attribute) for c in p.children]
            if all(is_attr):
                for attr in p.children:
                    if isinstance(attr, Attribute) and attr.name == 'id':
                        refs[attr.value] = target

    if len(refs) == 0:
        """
        Second heuristic - target is paragraph
            * Paragraph
                * ...
                * Attr(id, _)
        """
        if isinstance(el, marko.block.Paragraph) and len(children) >= 2:
            is_attr = [isinstance(c, Attribute) for c in el.children]
            if not all(is_attr):
                for attr in el.children:
                    if isinstance(attr, Attribute) and attr.name == 'id':
                        refs[attr.value] = el

    for child in children:
        refs = read_refs_from_ast(child) | refs

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
    elif isinstance(el, WikiLink):
        print(f"link> {el.page}")
    elif isinstance(el, marko.inline.CodeSpan):
        print(f"codespan>")
    elif isinstance(el, marko.block.CodeBlock):
        print(f"codeblock>")
    elif isinstance(el, BlockEmbed):
        print(f"block-embed>")
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


def read_attributes_from_ast(el: Element) -> dict[str, str]:
    attrs = {}
    children = get_children(el)
    if len(children) > 0:
        for candidate in get_children(children[0]):
            if isinstance(candidate, Attribute):
                attrs[candidate.name] = candidate.value
    return attrs


def enumerate_logseq_pages(logseq_path: str) -> Generator[PosixPath, None, None]:
    for file in Path(logseq_path).glob("pages/*.md"):
        yield file


def enumerate_logseq_journal(logseq_path: str) -> Generator[PosixPath, None, None]:
    for file in Path(logseq_path).glob("journals/*.md"):
        yield file


def embed_refs(el: Element, refs: dict[str, (str, Element)]):
    """
    Replaces all BlockRef's in a md-tree with referenced blocks
    """
    if isinstance(el, BlockElement) and hasattr(el, 'children'):
        for (idx, child) in enumerate(el.children):
            if isinstance(child, BlockRef):
                id = child.id
                if id in refs:
                    title, embed = refs[id]
                    el.children[idx] = BlockEmbed(title, embed)
            else:
                embed_refs(child, refs)


def escape_slug(title: str) -> str:
    return re.sub("[^a-zа-я0-9]", '-', title.lower())


def render_page(el: Element, title: str, f: IO):
    f.writelines(["---\n",
                  "unsafe: true\n",
                  f"title: {title}\n",
                  f"url: {NOTES_URL}/{escape_slug(title)}/\n",
                  "---\n",
                  md.render(el)])


def cli_render_single_page(args: argparse.Namespace):
    logseq_path = args.logseq_path
    note_path = args.note

    refs = read_all_refs(logseq_path)

    title = page_title_from_filename(note_path)
    ast = md.parse(open(note_path).read())
    embed_refs(ast, refs)
    render_page(ast, title, sys.stdout)


def cli_render_all_pages(args: argparse.Namespace):
    logseq_path = args.logseq_path
    output_path = args.output_path

    refs = read_all_refs(logseq_path)

    for page in enumerate_logseq_pages(logseq_path):
        ast = md.parse(open(page).read())
        attributes = read_attributes_from_ast(ast)

        if 'public' in attributes and attributes['public'] == 'true':
            title = page_title_from_filename(page)
            embed_refs(ast, refs)
            with open(output_path + "/" + basename(page), 'w') as f:
                render_page(ast, title, f)


def cli_render_ast(args: argparse.Namespace):
    ast = md.parse(open(args.note).read())
    render(ast)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    render = subparsers.add_parser('render')
    render.set_defaults(func=cli_render_single_page)
    render.add_argument('logseq_path', type=str,
                        help="path to logseq directory")
    render.add_argument('note', type=str, help="path to note to render")

    render = subparsers.add_parser('render-all')
    render.set_defaults(func=cli_render_all_pages)
    render.add_argument('logseq_path', type=str,
                        help="path to logseq directory")
    render.add_argument('output_path', type=str,
                        help="path to output")

    render = subparsers.add_parser('render-ast')
    render.set_defaults(func=cli_render_ast)
    render.add_argument('note', type=str, help="path to note to render")

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    NOTES_URL = "/notes"
    md = marko.Markdown(extensions=[LogSeqExtension])
    main()
