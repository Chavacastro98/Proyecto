from html.parser import HTMLParser
import sys

class StrictHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
        self.void_elements = {
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'
        }

    def handle_starttag(self, tag, attrs):
        if tag.lower() not in self.void_elements:
            self.stack.append((tag.lower(), self.getpos()))

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.void_elements:
            return
        if not self.stack:
            self.errors.append(f"Closing tag </{tag}> at {self.getpos()} with empty stack")
            return
        last_tag, pos = self.stack.pop()
        if last_tag != tag:
            self.errors.append(f"Mismatched tag: expected </{last_tag}> (opened at {pos}), got </{tag}> at {self.getpos()}")

parser = StrictHTMLParser()
with open(r'c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html', encoding='utf-8') as f:
    content = f.read()

parser.feed(content)

if parser.stack:
    print(f"Unclosed tags remaining ({len(parser.stack)}):")
    for t, pos in parser.stack[-10:]:
        print(f"  <{t}> opened at {pos}")
else:
    print("ALL TAGS PROPERLY CLOSED! HTML syntax is 100% clean.")

if parser.errors:
    print(f"Errors ({len(parser.errors)}):")
    for err in parser.errors[:10]:
        print(f"  {err}")
else:
    print("Zero mismatched tag errors!")
