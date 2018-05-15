#! /usr/bin/env python3

import argparse
import os
import re
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod

import pathlib
from typing import List
from halo import Halo


def md2tex(md: str, markdown_path: str = '/') -> str:
    # Return value to be assembled
    t = ''
    # Path of original markdown file
    markdown_path = pathlib.Path('/'.join(markdown_path.split('/')[:-1]))

    # For each line
    for line in md.strip().split('\n'):
        # Replace markdown image with latex image
        line = re.sub(r'!\[[^\]]*\]\(([^\)]+)\)', r'\\includegraphics[width=4.5cm]{{{}/\1}}'.format(
            # Path from .tex to markdown file, for image
            os.path.relpath(markdown_path, tmp)), line)
        # Latex quotes
        line = line.replace('"', "''")
        # Unify tabs
        line = line.replace('    ', '\t')
        # Append to return value
        t += line + '\n'

    # Matches an enumerations
    enumeration = re.compile(
        r'(\t*)1\. .*(\n\1((\d+\.)|(\t(-|\*|(\d+\.)))) .+)*')
    # Do for each enumeration
    while re.findall(enumeration, t):
        # Build replacement string
        nt = '\\begin{enumerate}\n'
        # Match the regex
        result = re.search(enumeration, t)
        # The string to be replaced
        replacement = result[0]
        # The indentation string (tabs)
        indent = result.group(1)
        # What to replace (don't destroy further indented sub-lists)
        item = r'^{}\d+\.'.format(indent)
        # Replace items with \item
        nt += re.sub(item, r'{}\t\\item'.format(indent),
                     replacement, flags=re.MULTILINE)
        nt += '\n\\end{enumerate}'
        # Replace it in the return string
        t = t.replace(replacement, nt)

    # Matches items
    itemize = re.compile(
        r'(\t*)(-|\*) .*(\n\1((-|\*)|(\t(-|\*|(\d+\.)))) .+)*')
    # Do for each enumeration
    while re.findall(itemize, t):
        # Build replacement string
        nt = '\\begin{itemize}\n'
        # Match the regex
        result = re.search(itemize, t)
        # The string to be replaced
        replacement = result[0]
        # The indentation string (tabs)
        indent = result.group(1)
        # What to replace (don't destroy further indented sub-lists)
        item = r'^{}(-|\*)'.format(indent)
        # Replace items with \item
        nt += re.sub(item, r'{}\t\\item'.format(indent),
                     replacement, flags=re.MULTILINE)
        nt += '\n\\end{itemize}'
        # Replace it in the return string
        t = t.replace(replacement, nt)

    return t


def md2txt(md: str):
    md = md.strip()
    md = md.replace('\n', '\n\t')
    md = '\t' + md
    md = re.sub(r'\n[\t ]*?\n', r'\n', md)
    md = re.sub(r'!\[[^\]]*\]\([^\)]+\)', r'<BILD>', md)
    md = re.sub(r'\$\$([^\n]+?)\$\$', r'\1', md)

    return md


class PrintableThing(ABC):

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def get_markdown(self) -> str:
        pass

    @abstractmethod
    def get_latex(self) -> str:
        pass


class MarkdownFile(PrintableThing):

    def __init__(self, directory: str):
        self.directory = directory
        self.elements = {}
        mode = ''

        with open(self.directory, 'r') as f:
            for line in f.readlines():
                if re.match('# .+', line):
                    mode = line[2:].strip()
                else:
                    if mode != '':
                        if mode not in self.elements:
                            self.elements[mode] = ''
                        self.elements[mode] += line

    def get_text(self) -> str:
        filename = self.directory.split('/')[-1]
        number = filename.rstrip('md')
        assert 'F' in self.elements
        t = number
        t += md2txt(self.elements['F'])
        a = 'A' in self.elements and args.answer
        e = 'E' in self.elements and args.explanation
        if a or e:
            t += '\n\n'
        if a and e:
            t += '\tAntwort:\n\n'
        if a:
            t += md2txt(self.elements['A'])
            if e:
                t += '\n\n'
        if a and e:
            t += '\tErklärung:\n\n'
        if e:
            t += md2txt(self.elements['E'])
        return t

    def get_markdown(self) -> str:
        filename = self.directory.split('/')[-1]
        path = '/'.join(self.directory.split('/')[:-1])
        number = filename.rstrip('md')
        assert 'F' in self.elements
        t = number + ' '
        for line in self.elements['F'].strip().split('\n'):
            if args.images:
                result = re.search(r'!\[.+?\]\((.+?)\)', line)
                if result:
                    image = result.group(1)
                    shutil.copyfile('{}/{}'.format(path, image), '{}/{}'.format(outputpath, image))
            else:
                line = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', r'![\1]({}/\2)'.format(
                    os.path.relpath(path, outputpath)), line)
            t += line
            t += '\n'
        a = 'A' in self.elements and args.answer
        e = 'E' in self.elements and args.explanation
        if a or e:
            t += '\n\n'
        if a:
            nt = ''
            for line in self.elements['A'].strip().split('\n'):
                indent = re.match(r'\s*', line).group()
                line = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', r'![\1]({}/\2)'.format(
                    os.path.relpath(path, outputpath)), line)
                nt += indent
                nt += line.lstrip()
                nt += '\n'
            t += nt[:-1]
            if e:
                t += '\n\n'
        if e:
            nt = ''
            for line in self.elements['E'].strip().split('\n'):
                indent = re.match(r'\s*', line).group()
                line = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', r'![\1]({}/\2)'.format(
                    os.path.relpath(path, outputpath)), line)
                nt += indent
                nt += line.lstrip()
                nt += '\n'
            t += nt[:-1]
        return t

    def get_latex(self) -> str:
        filename = self.directory.split('/')[-1]
        assert 'F' in self.elements
        a = 'A' in self.elements and args.answer
        e = 'E' in self.elements and args.explanation
        h = a and e

        t = ''
        if h:
            t += '\t\\textbf{Antwort:}\n\n'
        if a:
            for line in md2tex(self.elements['A'], self.directory).split('\n'):
                t += '\t'
                t += line
                t += '\n'
            t += '\n'
        if h:
            t += '\t\\textbf{Erklärung:}\n\n'
        if e:
            for line in md2tex(self.elements['E'], self.directory).split('\n'):
                t += '\t'
                t += line
                t += '\n'

        f = md2tex(self.elements['F'], self.directory)

        return '\n\t\question{{\n\t\t{}\n\t}}{{\n\t\t{}\n\t}}'.format(f.strip(), t.rstrip())


class Section(PrintableThing):

    def __init__(self, directory, is_first=True):
        self.is_first = is_first
        self.directory = directory
        self.children: List[PrintableThing] = []
        for d in sorted([d for d in os.listdir(self.directory) if re.match('\d+ .+', d) or re.match('\d+\.md', d)]):
            if re.match('\d+ .+', d):
                self.children.append(
                    Section('{}/{}'.format(self.directory, d), False))
            else:
                self.children.append(MarkdownFile(
                    '{}/{}'.format(self.directory, d)))

    def get_text(self) -> str:
        dirname = [x for x in self.directory.split(
            '/') if x != '' and x.lower()][-2 if self.is_first else -1]
        number = dirname.split(' ')[0]
        t = number
        if re.match(r'\d+', t):
            t += '. '
            t += ' '.join(dirname.split(' ')[1:])
        t += ':\n\n'
        for child in self.children:
            nt = ''
            for line in child.get_text().split('\n'):
                if re.match(r'\d+\. *', line) and re.match(r'\d+', number):
                    nt += number
                    nt += '.'
                nt += line
                nt += '\n'
            nt = nt[:-1]
            t += nt
            t += '\n\n'
        return t[:-2]

    def get_markdown(self) -> str:
        dirname = [x for x in self.directory.split(
            '/') if x != '' and x.lower()][-2 if self.is_first else -1]
        number = dirname.split(' ')[0]
        t = number
        if re.match('\d+', t):
            t += '. **'
            t += ' '.join(dirname.split(' ')[1:])
            t += '**'
        else:
            t = '# ' + t
        t += '\n\n'
        for child in self.children:
            t += child.get_markdown().replace('\n', '\n\t')
            t += '\n\n'
        return t[:-2]

    def get_latex(self) -> str:
        dirname = [x for x in self.directory.split(
            '/') if x != '' and x.lower()][-2 if self.is_first else -1]
        number = dirname.split(' ')[0]
        t = ''
        if re.match(r'\d+', number):
            t += '\\newChapter'
        else:
            # print('title?')
            pass
        for child in self.children:
            t += child.get_latex()
        return t


parser = argparse.ArgumentParser()
parser.add_argument('directory', help='the folder to be parsed')
parser.add_argument('-t', '--text', 
                    help='generate text file', action='store_true')
parser.add_argument('-m', '--markdown',
                    help='generate markdown file', action='store_true')
parser.add_argument(
    '-x', '--latex', help='generate latex file', action='store_true')
parser.add_argument('-a', '--answer', help='include answer',
                    action='store_true')
parser.add_argument('-e', '--explanation',
                    help='include explanation', action='store_true')
parser.add_argument('-i', '--images',
                    help='copies images to the markdown file, instead of referencing original', action='store_true')
parser.add_argument('-v', '--verbose',
                    help='print tex log', action='store_true')
args = parser.parse_args()

document = Section(args.directory)

parsepath = pathlib.Path(args.directory)
tmp = pathlib.Path(os.path.expanduser('~')) / 'textmp'
outputpath = parsepath / 'output'
outputpath.mkdir(exist_ok=True)
tmp.mkdir(exist_ok=True)

if args.text:
    with Halo(text='txt') as spinner:
        with open(outputpath / (parsepath.parts[-1] + '.txt'), 'w') as f:
            f.write(document.get_text())
        spinner.succeed()

if args.markdown:
    for file in [f for f in os.listdir(outputpath) if f.split('.')[-1].lower() in ['png', 'jpg', 'jpeg']]:
        os.remove('{}/{}'.format(outputpath, file))
    with Halo(text='markdown') as spinner:
        with open(outputpath / (parsepath.parts[-1] + '.md'), 'w') as f:
            f.write(document.get_markdown())
        spinner.succeed()

if args.latex:
    if not args.verbose:
        spinner = Halo(text='latex')
        spinner.start()
    with open(tmp / 'tmp.tex', 'w') as f:
        with open('{}/template.tex'.format(os.path.dirname(os.path.realpath(__file__))), 'r') as s:
            f.write(s.read().replace('<INSERT>', document.get_latex()))
    proc = subprocess.Popen(['cd {}; pdflatex tmp.tex'.format(
        str(tmp))], stdout=subprocess.PIPE, shell=True)
    if args.verbose:
        for line in iter(proc.stdout.readline, ''):
            sys.stdout.write(line.decode('utf8'))
    else:
        (out, err) = proc.communicate()
    shutil.move(tmp / 'tmp.pdf', outputpath / (parsepath.parts[-1] + '.pdf'))
    shutil.rmtree(tmp)
    if not args.verbose:
        spinner.succeed()
        spinner.stop()

if not (args.latex or args.markdown or args.latex):
    print('Seriously‽ You need to specify an output format!\nSee:\n')
    parser.print_help(sys.stderr)
