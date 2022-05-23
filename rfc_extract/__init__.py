#!/usr/bin/env python3
# Extract sourcecode or artwork content from an RFC XML file or markdown source.

import sys
import xml.sax
from xml.sax.saxutils import escape, quoteattr
from xml.sax.handler import ContentHandler

__version__ = '0.0.1'

class Block:
    def __init__(self, text, filename, line, column, typ):
        self.text = text
        self.filename = filename
        self.line = line
        self.column = column
        self.typ = typ

    def __str__(self):
        return self.text

    def _append(self, t):
        self.text = self.text + t


class _ExtractXML(ContentHandler):
    def __init__(self, filename, types, callback):
        ContentHandler.__init__(self)
        self.types = types
        self.filename = filename
        self.callback = callback
        self.current = None

    def currentTag(self):
        return next(reversed(self.tags), False)

    def startElement(self, tag, attrs):
        if tag not in ["artwork", "sourcecode"]:
            return
        typ = attrs["type"] if "type" in attrs else ""
        if not self.types or typ in self.types:
            self.current = Block(
                "",
                filename=self.filename,
                line=self._locator.getLineNumber(),
                column=self._locator.getColumnNumber(),
                typ=typ,
            )

    def endElement(self, tag):
        if self.current is None:
            return
        self.callback(self.current)
        self.current = None

    def characters(self, text):
        if self.current is not None:
            self.current._append(text)


def extract_md(f, types=[]):
    """extract() for Markdown documents."""

    ln = 0
    capture = False
    keep = True
    typ = ""
    text = ""
    with sys.stdin if f == "-" else open(f) as r:
        for line in r:
            ln = ln + 1
            block = line[:3] == "```" or line[:3] == "~~~"
            capture = block != capture
            if not capture:
                if text:
                    yield Block(text, filename=str(f), line=ln, column=0, typ=typ)
                    text = ""
                    typ = ""
                continue

            if block:
                typ = line[3:].lstrip("~`").strip()
                keep = not types or typ in types
            elif keep:
                text = text + line


def extract_xml(f, types=[]):
    """extract() for XML documents."""

    blocks = []

    def cb(b):
        blocks.append(b)

    parser = xml.sax.make_parser()
    parser.setContentHandler(_ExtractXML(str(f), types, cb))
    parser.parse(f)
    for b in blocks:
        yield b


def extract(f, types=[], ext=""):
    """
    Extract sourcecode or artwork blocks from a document.

    `types` is the list of type values to be extracted.
    An empty list will capture all blocks.

    `ext` is the extension of the file (which will be inferred if absent).
    """
    if ext:
        ext = ext.lower()
    else:
        ext = str(f).rsplit(".", 1)[1].lower()
    if ext == "md" or ext == "mkd":
        return extract_md(f, types)
    if ext == "xml":
        return extract_xml(f, types)
    raise NotImplementedError(f"file type '{typ}' not supported")


if __name__ == "__main__":
    def usage():
        print(
            f"Usage: {sys.argv[0]} [-t <types...>] [-x <md|xml>] file...",
            file=sys.stderr,
        )
        exit(2)

    files = []
    types = []
    ext = ""
    x, t = False, False
    for a in sys.argv[1:]:
        if t:
            for i in a.split(","):
                types.append(i.strip())
            t = False
            continue
        if x:
            ext = a.strip()
            x = False
            continue
        if a == "-x":
            x = True
        elif a == "-t":
            t = True
        elif a == "-":
            files.append("-")
        elif a[0] == "-":
            usage()
        else:
            files.append(a)

    if not files:
        usage()

    for f in files:
        found = False
        for b in extract(f, types, ext):
            print(f"{b.filename}:{b.line}:{b.column}:{b.typ}")
            print("    " + str(b).replace("\n", "\n    "))
            print()
            found = True
        if not found:
            print(f"{f}: no blocks found")
