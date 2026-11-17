import type { Result } from '@/api'
import mock from '@/mock/alerts.json'

// The API's Result plus fields the mock pulls from the raw PubMed records.
// The real API doesn't return these yet; they're optional so live search
// results (which lack them) still render.
export type Paper = Result & {
  journal?: string
  abstract?: string
  keywords?: string[]
  mesh?: string[]
  n_authors?: number
  doi?: string | null
}

export type Inbox = {
  id: number
  query: string
  created_at: string
  total: number
  papers: Paper[]
}

/** Start of the "new papers" window the mock results were fetched with. */
export const FEED_SINCE: string = mock.since

export function mockInboxes(): Inbox[] {
  return mock.alerts.map((a) => ({
    id: a.id,
    query: a.query,
    created_at: a.created_at,
    total: a.total,
    papers: a.results as Paper[],
  }))
}

/** PMIDs that start out read, so the mock has a mix of read and unread. */
export function initialRead(inboxes: Inbox[]): Set<string> {
  return new Set(inboxes.flatMap((i) => i.papers.slice(-6).map((p) => p.pmid)))
}

// Publication types worth calling out, strongest evidence first.
const EVIDENCE: [string, string][] = [
  ['Meta-Analysis', 'Meta-analysis'],
  ['Systematic Review', 'Systematic review'],
  ['Randomized Controlled Trial', 'RCT'],
  ['Clinical Trial', 'Clinical trial'],
  ['Review', 'Review'],
  ['Case Reports', 'Case report'],
  ['Preprint', 'Preprint'],
]

/** Short labels for the notable publication types, in evidence order. */
export function studyTags(p: Paper): string[] {
  return EVIDENCE.filter(([t]) => p.pub_types.includes(t)).map(([, label]) => label)
}

export const isStrongEvidence = (tag: string) =>
  tag === 'Meta-analysis' || tag === 'Systematic review' || tag === 'RCT'

const parse = (d: string) => new Date(d.length === 10 ? `${d}T00:00:00` : d)

/** "Oct 14" style date, like an inbox row. */
export const shortDate = (d: string) =>
  parse(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })

export const longDate = (d: string) =>
  parse(d).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })

/** PubMed journal names are often lowercase ("The Journal of nutrition"). */
export const journalName = (p: Paper) => {
  const j = p.journal?.split(' : ')[0].split(' = ')[0]
  return j ? j.charAt(0).toUpperCase() + j.slice(1) : 'PubMed'
}

/** Start of the abstract, for the list preview. */
export const snippet = (p: Paper) => p.abstract?.slice(0, 220)
