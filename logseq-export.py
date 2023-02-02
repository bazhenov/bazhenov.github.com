import marko
import sys
import os

def render_html(file):
    content = open(file).read()
    return marko.convert(content)

def render(el: marko.block.Element, depth=0):
    if isinstance(el, marko.block.BlockElement):
        for c in el.children:
            print(("  " * depth) + f"({el.get_type()})")
            render(c, depth=depth + 1)
    elif isinstance(el, marko.block.inline.InlineElement):
        print(("  " * depth) + f"({el.get_type()} - {el.children})")
    else:
        print(("  " * depth) + f"({type(el)})")


if __name__ == "__main__":
    dir_path = sys.argv[1]

    for file in os.listdir(dir_path):
        if file.endswith(".md"):
            new_file_name
            print(f"{file}")
    # content = open(file_path).read()
    # parser = marko.Parser()
    # ast = parser.parse(content)
    # print(f"{render(ast)}")
