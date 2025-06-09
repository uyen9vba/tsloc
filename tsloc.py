#!/usr/bin/env python

import os
import sys
import argparse
import math
from colorama import Fore, Back, Style

args = None

class Node:
    def __init__(self, name="", fd="directory", lines=0, files=None, exts=None, nodes=None):
        self.name = name
        self.fd = fd
        self.lines = lines
        self.files = files if files is not None else []
        self.exts = exts if exts is not None else []
        self.nodes = nodes if nodes is not None else []

    def child(self, child_node):
        self.nodes.append(child_node)

def tsloc(directory=None, depth=0, root=False):
    node = Node()

    entries = []
    try:
        for e in os.scandir(directory):
            if e.name.startswith(".") and not args.dotfiles:
                continue
            if e.is_dir() and e.name in args.ignore_dir:
                continue
            entries.append(e)
    except PermissionError:
        return tree

    # alphabetic, directories first
    entries.sort(key=lambda e: e.name)
    entries.sort(key=lambda e: (not e.is_dir(), e.name))

    for entry in entries:

        if entry.is_dir():
            node.name = entry.name
            node.fd = "directory"

            print(Style.RESET_ALL + f"{node.name}")

            subnode = tsloc(entry.path, depth + 1, root=False)
            node.files.append(subnode.name)
            node.lines += subnode.lines
            node.nodes.append(subnode)

            name = entry.name
            name = "  " * depth + name
            name = f"{name:<{24}}"
            files = len(subnode.files) if subnode.files != None else ""
            files = f"files {files:<4}"
            lines = subnode.lines
            lines = f"lines {lines:<6}"
            exts_clean = list(dict.fromkeys(subnode.exts))
            exts_clean.sort(key=lambda x: subnode.exts.count(x), reverse=True)
            exts = ", ".join(f"{subnode.exts.count(a)}*{a}" for a in exts_clean)

            # calculate how many lines we need to go back to parent directory
            def recursive(node):
                total = 0
                stack = [node]
                while stack:
                    current = stack.pop()
                    for s in getattr(current, 'nodes', []):
                        if s.fd == "directory" and not args.files:
                            total += 1
                        if s.fd == "file" and args.files:
                            total += 1
                        stack.append(s)
                return total
            n = recursive(subnode) + 1

            con = Style.RESET_ALL + f"{name} {files} " + Fore.YELLOW + f"{lines} " + Fore.GREEN + f"{exts}"

            sys.stdout.write(f"\x1b[{n}A")

            # cut length to 1 line from too many file extensions
            style = Style.RESET_ALL + Fore.YELLOW + Fore.GREEN
            con_len = len(con) - len(style)
            width = os.get_terminal_size().columns
            if con_len // width > 0:
                cut_pos = con.rfind(",")
                while cut_pos > width - 3:
                    cut_pos = con.rfind(",", 0, cut_pos)
                con = con[:len(style)+cut_pos] + "..."

            sys.stdout.write(f"\x1b[2K{con}\r")
            sys.stdout.write(f"\x1b[{n}B")
            sys.stdout.flush()
        else:
            try:
                subnode = Node()
                with open(entry.path, 'r', encoding='utf-8', errors='ignore') as f:
                    _, ext = os.path.splitext(entry.name)
                    subnode.name = entry.name
                    subnode.fd = "file"
                    subnode.files = None
                    subnode.lines = sum(1 for _ in f)
                    subnode.exts = ext
                    
                    node.lines += subnode.lines
                    node.files.append(subnode.name)
                    node.exts.append(ext)
                    node.nodes.append(subnode)

                if args.files:
                    name = entry.name
                    name = "  " * depth + name
                    name = f"{name:<{35}}"
                    lines = subnode.lines
                    lines = Fore.YELLOW + f"lines {lines:<6}"
                    print(Style.RESET_ALL + f"{name} {lines}")
            except Exception:
                print("TODO") # TODO

    return node

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tree view with line counts.")
    parser.add_argument('directory', nargs='?', default='.', help='Root directory')
    parser.add_argument('--files', action='store_true', default=False, help='List files. Default is off.')
    parser.add_argument('--dotfiles', action='store_true', default=False, help='List dot files. Default is off.')
    parser.add_argument('--ignore-dir', nargs='+', help='List of directories to ignore')
    args = parser.parse_args()
    node = tsloc(directory=args.directory, depth=0, root=True)

