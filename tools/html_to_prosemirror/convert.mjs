#!/usr/bin/env node
// Reads page.document HTML on stdin, writes ProseMirror JSON (as produced by the
// same TipTap schema the Nuxt editor uses) to stdout. Invoked as a subprocess from
// app/tools/prosemirror.py -- kept as a standalone CLI so the Python side never has
// to embed a JS runtime itself.
import { generateJSON } from '@tiptap/html'
import Document from '@tiptap/extension-document'
import Paragraph from '@tiptap/extension-paragraph'
import Text from '@tiptap/extension-text'
import Heading from '@tiptap/extension-heading'
import Bold from '@tiptap/extension-bold'
import Italic from '@tiptap/extension-italic'
import Underline from '@tiptap/extension-underline'
import BulletList from '@tiptap/extension-bullet-list'
import OrderedList from '@tiptap/extension-ordered-list'
import ListItem from '@tiptap/extension-list-item'
import Image from '@tiptap/extension-image'
import { Table, TableRow, TableCell, TableHeader } from '@tiptap/extension-table'
import HardBreak from '@tiptap/extension-hard-break'
import Link from '@tiptap/extension-link'
import Superscript from '@tiptap/extension-superscript'
import Subscript from '@tiptap/extension-subscript'
import { PoTaxonomy } from './po-taxonomy.mjs'

export const extensions = [
  Document,
  Paragraph,
  Text,
  Heading,
  Bold,
  Italic,
  Underline,
  BulletList,
  OrderedList,
  ListItem,
  Image,
  Table.configure({ resizable: false }),
  TableRow,
  TableCell,
  TableHeader,
  HardBreak,
  Link,
  Superscript,
  Subscript,
  PoTaxonomy,
]

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = ''
    process.stdin.setEncoding('utf8')
    process.stdin.on('data', (chunk) => { data += chunk })
    process.stdin.on('end', () => resolve(data))
    process.stdin.on('error', reject)
  })
}

const html = await readStdin()
const json = generateJSON(html, extensions)
process.stdout.write(JSON.stringify(json))
