import { Node, mergeAttributes } from '@tiptap/core'

/**
 * Placeholder block embedded where a quiz table was extracted from the source HTML.
 * Named after the taxonomy, not the content: SetTaxonomy is already a page-type-
 * agnostic grouping mechanism elsewhere in this app (TestSessionService,
 * FlashcardService, QuizService all just walk taxonomy membership and branch on
 * each page's own id_type), so this stays one reusable node -- "embed this
 * taxonomy's pages here" -- instead of a po-quiz/po-characters/po-dates node per
 * content type. The Nuxt renderer fetches the taxonomy's member pages and decides
 * how to render each by its own id_type/id_sub_type.
 * The Python side replaces the matched quiz <table> (+ marker paragraph + answer
 * key) with `<div data-type="po-taxonomy" data-taxonomy-id="...">` before handing
 * the HTML to this converter, so this node only needs to round-trip that marker
 * into `{ type: "po-taxonomy", attrs: { taxonomy_id } }`.
 */
export const PoTaxonomy = Node.create({
  name: 'po-taxonomy',
  group: 'block',
  atom: true,
  selectable: false,

  addAttributes() {
    return {
      taxonomy_id: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-taxonomy-id'),
        renderHTML: (attributes) => ({ 'data-taxonomy-id': attributes.taxonomy_id }),
      },
    }
  },

  parseHTML() {
    return [{ tag: 'div[data-type="po-taxonomy"]' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, { 'data-type': 'po-taxonomy' })]
  },
})
