import { InboxIcon, Search01Icon, StarIcon } from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'

import { Badge } from '@/components/ui/badge'
import { Empty, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { isStrongEvidence, journalName, type Paper, shortDate, snippet, studyTags } from '@/lib/papers'
import { cn } from '@/lib/utils'

/** A paper as it appears in a list, tagged with the alert it came from. */
export type Item = { paper: Paper; alertId: number; alertQuery: string }

type Props = {
  title: string
  subtitle: string
  items: Item[]
  showSource: boolean
  selected: string | null
  onSelect: (pmid: string) => void
  isRead: (pmid: string) => boolean
  isStarred: (pmid: string) => boolean
  filter: 'all' | 'unread'
  onFilterChange: (f: 'all' | 'unread') => void
  search: string
  onSearchChange: (s: string) => void
  loading?: boolean
}

export function PaperList({
  title,
  subtitle,
  items,
  showSource,
  selected,
  onSelect,
  isRead,
  isStarred,
  filter,
  onFilterChange,
  search,
  onSearchChange,
  loading,
}: Props) {
  return (
    <div className="flex h-full min-w-0 flex-col">
      <div className="flex items-start gap-2 px-4 pt-3 pb-2">
        <SidebarTrigger className="-ml-1.5 mt-0.5" />
        <div className="min-w-0 flex-1">
          <h1 className="truncate font-heading text-lg leading-tight font-semibold first-letter:uppercase">
            {title}
          </h1>
          <p className="truncate text-xs text-muted-foreground">{subtitle}</p>
        </div>
        <Tabs value={filter} onValueChange={(v) => onFilterChange(v as 'all' | 'unread')}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="unread">Unread</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      <div className="px-4 pb-3">
        <div className="relative">
          <HugeiconsIcon
            icon={Search01Icon}
            className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
          />
          <Input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Filter this inbox"
            className="pl-8"
          />
        </div>
      </div>
      <Separator />

      <ScrollArea className="min-h-0 flex-1">
        {loading ? (
          <ListSkeleton />
        ) : items.length === 0 ? (
          <Empty className="py-16">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <HugeiconsIcon icon={InboxIcon} />
              </EmptyMedia>
              <EmptyTitle>{search || filter === 'unread' ? 'Nothing matches' : 'No papers'}</EmptyTitle>
            </EmptyHeader>
          </Empty>
        ) : (
          <ul className="flex flex-col gap-1 p-2">
            {items.map(({ paper, alertQuery }) => {
              const read = isRead(paper.pmid)
              const tags = studyTags(paper)
              return (
                <li key={paper.pmid}>
                  <button
                    type="button"
                    onClick={() => onSelect(paper.pmid)}
                    data-selected={selected === paper.pmid || undefined}
                    className={cn(
                      'group flex w-full flex-col gap-1 rounded-2xl px-3 py-2.5 text-left text-sm transition-colors outline-none hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/30',
                      'data-selected:bg-primary/8 data-selected:hover:bg-primary/12 dark:data-selected:bg-primary/15',
                    )}
                  >
                    <div className="flex w-full items-center gap-2">
                      <span
                        aria-label={read ? undefined : 'Unread'}
                        className={cn('size-2 shrink-0 rounded-full', read ? 'bg-transparent' : 'bg-primary')}
                      />
                      <span
                        className={cn(
                          'min-w-0 flex-1 truncate text-xs',
                          read ? 'text-muted-foreground' : 'font-semibold text-foreground',
                        )}
                      >
                        {journalName(paper)}
                      </span>
                      {isStarred(paper.pmid) && (
                        <HugeiconsIcon icon={StarIcon} className="size-3.5 fill-amber-400 text-amber-400" />
                      )}
                      <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
                        {shortDate(paper.date)}
                      </span>
                    </div>
                    <p
                      className={cn(
                        'line-clamp-2 pl-4 leading-snug',
                        read ? 'text-foreground/80' : 'font-semibold text-foreground',
                      )}
                    >
                      {paper.title}
                    </p>
                    {paper.abstract && (
                      <p className="line-clamp-2 pl-4 text-xs leading-relaxed text-muted-foreground">
                        {snippet(paper)}
                      </p>
                    )}
                    {(tags.length > 0 || showSource) && (
                      <div className="flex flex-wrap items-center gap-1 pt-1 pl-4">
                        {showSource && (
                          <Badge variant="secondary" className="max-w-56 justify-start font-normal">
                            <span className="truncate">{alertQuery}</span>
                          </Badge>
                        )}
                        {tags.map((t) => (
                          <Badge key={t} variant={isStrongEvidence(t) ? 'default' : 'outline'}>
                            {t}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </ScrollArea>
    </div>
  )
}

function ListSkeleton() {
  return (
    <div className="flex flex-col gap-4 p-4">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="flex animate-pulse flex-col gap-2">
          <div className="h-3 w-1/3 rounded bg-muted" />
          <div className="h-4 w-full rounded bg-muted" />
          <div className="h-3 w-5/6 rounded bg-muted" />
        </div>
      ))}
    </div>
  )
}
