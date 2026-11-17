import { useCallback, useEffect, useMemo, useState } from 'react'

import { search as searchApi } from '@/api'
import { AppSidebar, type View } from '@/components/app-sidebar'
import { type Item, PaperList } from '@/components/paper-list'
import { PaperView } from '@/components/paper-view'
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useIsMobile } from '@/hooks/use-mobile'
import { FEED_SINCE, type Inbox, initialRead, mockInboxes, type Paper, shortDate } from '@/lib/papers'

// UI mock: alerts and their papers come from src/mock/alerts.json, and
// read/starred/archived state lives only in memory. "New alert" does try the
// live /search endpoint so new inboxes have something in them.

function useSet(initial: () => Set<string>) {
  const [set, setSet] = useState(initial)
  const toggle = useCallback(
    (key: string, on?: boolean) =>
      setSet((prev) => {
        const next = new Set(prev)
        if (on ?? !next.has(key)) next.add(key)
        else next.delete(key)
        return next
      }),
    [],
  )
  return [set, toggle] as const
}

function useDarkMode() {
  const [dark, setDark] = useState(() => {
    try {
      const saved = localStorage.getItem('theme')
      if (saved) return saved === 'dark'
    } catch {
      /* storage unavailable */
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    try {
      localStorage.setItem('theme', dark ? 'dark' : 'light')
    } catch {
      /* storage unavailable */
    }
  }, [dark])
  return [dark, () => setDark((d) => !d)] as const
}

function App() {
  const [inboxes, setInboxes] = useState<Inbox[]>(mockInboxes)
  const [loading, setLoading] = useState<Set<number>>(new Set())
  const [view, setView] = useState<View>({ kind: 'all' })
  const [selected, setSelected] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')
  const [query, setQuery] = useState('')
  const [read, toggleRead] = useSet(() => initialRead(inboxes))
  const [starred, toggleStar] = useSet(() => new Set())
  const [archived, toggleArchived] = useSet(() => new Set())
  const [dark, toggleDark] = useDarkMode()
  const isMobile = useIsMobile()

  // Every paper across all alerts, newest first. A paper that matches more
  // than one alert shows up once, under the first alert it matched.
  const everything = useMemo(() => {
    const seen = new Set<string>()
    const out: Item[] = []
    for (const inbox of inboxes)
      for (const paper of inbox.papers)
        if (!seen.has(paper.pmid)) {
          seen.add(paper.pmid)
          out.push({ paper, alertId: inbox.id, alertQuery: inbox.query })
        }
    return out.sort((a, b) => b.paper.date.localeCompare(a.paper.date) || b.paper.score - a.paper.score)
  }, [inboxes])

  const currentInbox = view.kind === 'alert' ? inboxes.find((i) => i.id === view.id) : undefined

  const items = useMemo(() => {
    let list: Item[]
    if (view.kind === 'alert') {
      // Within one alert, keep the ranker's order.
      list = (currentInbox?.papers ?? []).map((paper: Paper) => ({
        paper,
        alertId: view.id,
        alertQuery: currentInbox!.query,
      }))
    } else if (view.kind === 'starred') {
      list = everything.filter((i) => starred.has(i.paper.pmid))
    } else {
      list = everything
    }
    list = list.filter((i) => !archived.has(i.paper.pmid))
    // Keep the open paper in the Unread list even though opening marks it read.
    if (filter === 'unread') list = list.filter((i) => !read.has(i.paper.pmid) || i.paper.pmid === selected)
    const q = query.trim().toLowerCase()
    if (q)
      list = list.filter(({ paper: p }) =>
        [p.title, p.abstract, p.journal, ...(p.keywords ?? [])].some((s) => s?.toLowerCase().includes(q)),
      )
    return list
  }, [view, currentInbox, everything, starred, archived, filter, read, selected, query])

  const unreadIn = useCallback(
    (inbox: Inbox) => inbox.papers.filter((p) => !read.has(p.pmid) && !archived.has(p.pmid)).length,
    [read, archived],
  )
  const totalUnread = everything.filter((i) => !read.has(i.paper.pmid) && !archived.has(i.paper.pmid)).length

  const index = items.findIndex((i) => i.paper.pmid === selected)
  const current = index >= 0 ? items[index] : null

  const open = useCallback(
    (pmid: string | null) => {
      setSelected(pmid)
      if (pmid) toggleRead(pmid, true)
    },
    [toggleRead],
  )

  function changeView(v: View) {
    setView(v)
    setSelected(null)
    setQuery('')
  }

  function archive() {
    if (!current) return
    const next = items[index + 1] ?? items[index - 1]
    toggleArchived(current.paper.pmid, true)
    open(next && next.paper.pmid !== current.paper.pmid ? next.paper.pmid : null)
  }

  function createAlert(q: string) {
    const id = Math.max(0, ...inboxes.map((i) => i.id)) + 1
    setInboxes((prev) => [...prev, { id, query: q, created_at: new Date().toISOString(), total: 0, papers: [] }])
    changeView({ kind: 'alert', id })
    setLoading((s) => new Set(s).add(id))
    searchApi(q, { since: FEED_SINCE })
      .then((r) =>
        setInboxes((prev) => prev.map((i) => (i.id === id ? { ...i, total: r.total, papers: r.results } : i))),
      )
      .catch(() => {
        /* API offline: leave the inbox empty */
      })
      .finally(() =>
        setLoading((s) => {
          const next = new Set(s)
          next.delete(id)
          return next
        }),
      )
  }

  function deleteAlert(id: number) {
    setInboxes((prev) => prev.filter((i) => i.id !== id))
    if (view.kind === 'alert' && view.id === id) changeView({ kind: 'all' })
  }

  // Mail-style keyboard shortcuts.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.metaKey || e.ctrlKey || e.altKey) return
      const t = e.target as HTMLElement
      if (t.closest('input, textarea, [role="dialog"], [role="menu"]')) return
      const move = (d: number) => {
        const next = items[index < 0 ? 0 : index + d]
        if (next) open(next.paper.pmid)
      }
      switch (e.key) {
        case 'j':
        case 'ArrowDown':
          move(1)
          break
        case 'k':
        case 'ArrowUp':
          move(-1)
          break
        case 's':
          if (current) toggleStar(current.paper.pmid)
          break
        case 'u':
          if (current) toggleRead(current.paper.pmid)
          break
        case 'e':
          archive()
          break
        case 'Escape':
          setSelected(null)
          break
        default:
          return
      }
      e.preventDefault()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  let title = 'All alerts'
  let subtitle = `${totalUnread} unread across ${inboxes.length} alerts`
  if (view.kind === 'starred') {
    title = 'Starred'
    subtitle = `${starred.size} starred ${starred.size === 1 ? 'paper' : 'papers'}`
  } else if (currentInbox) {
    title = currentInbox.query
    subtitle = loading.has(currentInbox.id)
      ? 'Searching for new papers…'
      : `${unreadIn(currentInbox)} unread · ${currentInbox.total.toLocaleString()} matches since ${shortDate(FEED_SINCE)}`
  }

  const list = (
    <PaperList
      title={title}
      subtitle={subtitle}
      items={items}
      showSource={view.kind !== 'alert'}
      selected={selected}
      onSelect={open}
      isRead={(p) => read.has(p)}
      isStarred={(p) => starred.has(p)}
      filter={filter}
      onFilterChange={setFilter}
      search={query}
      onSearchChange={setQuery}
      loading={currentInbox ? loading.has(currentInbox.id) : false}
    />
  )

  const reader = (
    <PaperView
      item={current}
      read={current ? read.has(current.paper.pmid) : false}
      starred={current ? starred.has(current.paper.pmid) : false}
      onToggleRead={() => current && toggleRead(current.paper.pmid)}
      onToggleStar={() => current && toggleStar(current.paper.pmid)}
      onArchive={archive}
      onPrev={index > 0 ? () => open(items[index - 1].paper.pmid) : undefined}
      onNext={index >= 0 && index < items.length - 1 ? () => open(items[index + 1].paper.pmid) : undefined}
      onBack={isMobile ? () => setSelected(null) : undefined}
    />
  )

  return (
    <TooltipProvider>
      <SidebarProvider className="h-svh">
        <AppSidebar
          inboxes={inboxes}
          view={view}
          onViewChange={changeView}
          unread={unreadIn}
          totalUnread={totalUnread}
          starredCount={starred.size}
          dark={dark}
          onToggleDark={toggleDark}
          onCreateAlert={createAlert}
          onDeleteAlert={deleteAlert}
        />
        <SidebarInset className="min-w-0 overflow-hidden">
          {isMobile ? (
            current ? reader : list
          ) : (
            <ResizablePanelGroup orientation="horizontal">
              <ResizablePanel defaultSize="40%" minSize="28%" maxSize="60%">
                {list}
              </ResizablePanel>
              <ResizableHandle />
              <ResizablePanel defaultSize="60%" minSize="35%">
                {reader}
              </ResizablePanel>
            </ResizablePanelGroup>
          )}
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  )
}

export default App
