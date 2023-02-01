"""
Simple script for migration .md files from Jekyll to Hugo. Basically do 2 things:

1. writes proper date attribute to frontmatter of .md file based on file name.
2. write proper url into .md frontmatter section for backward compatibility with Jekyll urls

"""
import sys
import os.path as p
import re


def migrate(file_path):
    file_name = p.basename(file_path)

    m = re.match("^([0-9]{4}-[0-9]{2}-[0-9]{2})-(.+).md$", file_name)
    if not m:
        raise ValueError(
            "File name should start from date in format 2023-12-01-title.md")

    date = m.group(1)
    slug = m.group(2)
    content = open(file_path).read().splitlines()

    if not content:
        raise ValueError(f"File is empty")

    if content[0] != "---":
        raise ValueError(f"File should start with Front Matter section")

    if content.index("---", 1) <= 1:
        raise ValueError(
            f"File should contain Front Matter section end delimeter")

    url = f"/blog/{date.replace('-', '/')}/{slug}.html"
    content[1:1] = [f"url: {url}"]

    content[1:1] = [f"date: {date}"]

    content = "\n".join(content) + "\n"
    open(file_path, 'w').write(content)


if __name__ == "__main__":
    for path in sys.argv[1:]:
        print(f"Processing: {path}")
        migrate(path)
