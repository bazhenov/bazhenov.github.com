import marko
from marko.inline import InlineElement
from marko.block import BlockElement, Element
import marko.inline
from more_itertools import partition
from re import Match
import sys
import os


class BlockRef(InlineElement):
    pattern = r"^\(\(([^)]+)\)\)$"
    parse_children = False
    id = None

    def __init__(self, match: Match) -> None:
        self.id = match.group(1)


class Attribute(InlineElement):
    pattern = r"(?:^|\n)([a-zA-Z]+)::\s*([a-zA-Z0-9_-]+)"
    parse_children = False
    name = None
    value = None

    def __init__(self, match: Match) -> None:
        self.name = match.group(1)
        self.value = match.group(2)


class RendererMixins:
    def render_block_ref(self, el: BlockRef):
        return f"REFERENCE: {el.id}"

    def render_attribute(self, el: Attribute):
        return f"A: {el.name}={el.value}"


class LogSeqExtension:
    elements = [BlockRef, Attribute]
    renderer_mixins = [RendererMixins]


class Node:
    name = None
    children = []
    attributes = {}


class TextNode(Node):
    name = 'text'
    text = None


class RefNode(Node):
    name = 'ref'
    id = None


def map_ast(el: Element) -> Node:
    result = Node()
    result.name = type(el)
    if isinstance(el, marko.block.Document):
        pass
    elif isinstance(el, marko.inline.RawText):
        if isinstance(el.children, str):
            result = TextNode()
            result.text = el.children
    elif isinstance(el, BlockRef):
        result = RefNode()
        result.id = el.id
    else:
        # raise ValueError(f"Invalid element type: {type(el)}")
        pass
    if isinstance(el, BlockElement) and not isinstance(el, marko.block.BlankLine):
        def is_attribute(e): return isinstance(e, Attribute)
        children, attributes = partition(is_attribute, el.children)
        children = [c for c in children]

        result.attributes = {a.name: a.value for a in attributes}
        # print(f"{len(children)}, {len(result.attributes)}, {result.attributes}, {type(el)}")

        result.children = [map_ast(child) for child in children]
        result.children = [simplify(child) for child in result.children]
    return result


def simplify(el: Node) -> Node:
    # Simplify tree bottom up
    el.children = [simplify(child) for child in el.children]

    # Removing intermediate nodes from tree, but saving attributes
    if len(el.children) == 1:
        result = el.children[0]
        result.attributes = result.attributes | el.attributes
        return result

    # merging empty siblings with text nodes
    # for i in range(len(el.children) - 1):
    #     left, right = el.children[i], el.children[i+1]
    #     if isinstance(left, TextNode) and not isinstance(right, TextNode) and len(left.children) == 0:
    #         left.attributes = left.attributes | right.attributes
    #         left.children = right.children
    #         del el.children[i + 1]
    return el


def render_node(el: Node, depth=0):
    prefix = "      " * depth
    if isinstance(el, TextNode):
        print(f"{prefix}{el.text}")
    elif isinstance(el, RefNode):
        print(f"{prefix}*{el.id}")
    else:
        print(f"{prefix}node: {el.name}")

    for (name, value) in el.attributes.items():
        print(f"{prefix}--- {name}={value}")

    for child in el.children:
        render_node(child, depth+1)


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
    elif isinstance(el, marko.inline.LineBreak):
        print(prefix)
    elif isinstance(el, marko.block.BlankLine):
        print(prefix)
    elif isinstance(el, BlockRef):
        print(f"*{el.id}")
    elif isinstance(el, marko.inline.RawText):
        print(el.children)
    elif isinstance(el, Attribute):
        print(f"attr: {el.name}={el.value}")
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


if __name__ == "__main__":
    # input = sys.argv[1]
    # output_path = "./content/notes"
    # migrate_logseq_files(input, output_path)

    file_path = sys.argv[1]
    content = open(file_path).read()
    md = marko.Markdown(extensions=[LogSeqExtension])
    ast = md.parse(content)
    # ast = map_ast(ast)
    print(f"{md.render(ast)}")
