import {
  Archive02Icon,
  ArrowDown01Icon,
  ArrowLeft01Icon,
  ArrowUp01Icon,
  BookOpen01Icon,
  Calendar03Icon,
  LinkSquare02Icon,
  Mail01Icon,
  MailOpen01Icon,
  StarIcon,
  UserGroupIcon,
} from '@hugeicons/core-free-icons'
import { HugeiconsIcon, type IconSvgElement } from '@hugeicons/react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Kbd } from '@/components/ui/kbd'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { Item } from '@/components/paper-list'
import { isStrongEvidence, journalName, longDate, studyTags } from '@/lib/papers'
import { cn } from '@/lib/utils'

type Props = {
  item: Item | null
  read: boolean
  starred: boolean
  onToggleRead: () => void
  onToggleStar: () => void
  onArchive: () => void
  onPrev?: () => void
  onNext?: () => void
  onBack?: () => void
}

export function PaperView({
  item,
  read,
  starred,
  onToggleRead,
  onToggleStar,
  onArchive,
  onPrev,
  onNext,
  onBack,
}: Props) {
  if (!item) {
    return <div className="h-full" />
  }

  const { paper, alertQuery } = item
  const tags = studyTags(paper)

  return (
    <div className="flex h-full min-w-0 flex-col">
      <div className="flex h-14 shrink-0 items-center gap-1 px-3">
        {onBack && <ToolbarButton icon={ArrowLeft01Icon} label="Back to list" onClick={onBack} />}
        <ToolbarButton icon={Archive02Icon} label="Archive" shortcut="e" onClick={onArchive} />
        <ToolbarButton
          icon={read ? Mail01Icon : MailOpen01Icon}
          label={read ? 'Mark as unread' : 'Mark as read'}
          shortcut="u"
          onClick={onToggleRead}
        />
        <ToolbarButton
          icon={StarIcon}
          label={starred ? 'Unstar' : 'Star'}
          shortcut="s"
          onClick={onToggleStar}
          iconClassName={cn(starred && 'fill-amber-400 text-amber-400')}
        />
        <div aria-hidden className="mx-1 h-5 w-px bg-border" />
        <ToolbarButton icon={ArrowUp01Icon} label="Previous" shortcut="k" onClick={onPrev} />
        <ToolbarButton icon={ArrowDown01Icon} label="Next" shortcut="j" onClick={onNext} />
        <div className="flex-1" />
        <Button
          variant="outline"
          size="sm"
          nativeButton={false}
          render={<a href={paper.url} target="_blank" rel="noreferrer" />}
        >
          Open in PubMed
          <HugeiconsIcon icon={LinkSquare02Icon} data-icon="inline-end" />
        </Button>
      </div>
      <Separator />

      <ScrollArea className="min-h-0 flex-1">
        <article className="mx-auto flex max-w-3xl flex-col gap-5 px-6 py-6">
          <header className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-1.5">
              <Badge variant="secondary" className="max-w-full justify-start font-normal">
                <span className="truncate">{alertQuery}</span>
              </Badge>
              {tags.map((t) => (
                <Badge key={t} variant={isStrongEvidence(t) ? 'default' : 'outline'}>
                  {t}
                </Badge>
              ))}
            </div>
            <h2 className="font-heading text-2xl leading-tight font-semibold text-balance">{paper.title}</h2>
            <dl className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
              <Meta icon={BookOpen01Icon} label="Journal">
                {journalName(paper)}
              </Meta>
              <Meta icon={Calendar03Icon} label="Added">
                {longDate(paper.date)}
              </Meta>
              {!!paper.n_authors && (
                <Meta icon={UserGroupIcon} label="Authors">
                  {paper.n_authors} {paper.n_authors === 1 ? 'author' : 'authors'}
                </Meta>
              )}
            </dl>
          </header>

          <Separator />

          <section className="flex flex-col gap-2">
            <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Abstract</h3>
            <p className="leading-relaxed text-pretty whitespace-pre-line">{paper.abstract || '—'}</p>
          </section>

          {!!paper.keywords?.length && <TermList title="Keywords" terms={paper.keywords} />}
          {!!paper.mesh?.length && <TermList title="MeSH terms" terms={paper.mesh} />}

          <p className="text-xs text-muted-foreground tabular-nums">
            Score {paper.score} · PMID {paper.pmid}
            {paper.doi && <> · DOI {paper.doi}</>}
          </p>
        </article>
      </ScrollArea>
    </div>
  )
}

function ToolbarButton({
  icon,
  label,
  shortcut,
  onClick,
  iconClassName,
}: {
  icon: IconSvgElement
  label: string
  shortcut?: string
  onClick?: () => void
  iconClassName?: string
}) {
  return (
    <Tooltip>
      <TooltipTrigger
        render={<Button variant="ghost" size="icon-sm" aria-label={label} disabled={!onClick} onClick={onClick} />}
      >
        <HugeiconsIcon icon={icon} className={iconClassName} />
      </TooltipTrigger>
      <TooltipContent>
        {label}
        {shortcut && <Kbd className="ml-1">{shortcut}</Kbd>}
      </TooltipContent>
    </Tooltip>
  )
}

function Meta({ icon, label, children }: { icon: IconSvgElement; label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-1.5">
      <dt className="sr-only">{label}</dt>
      <HugeiconsIcon icon={icon} className="size-4" />
      <dd>{children}</dd>
    </div>
  )
}

function TermList({ title, terms }: { title: string; terms: string[] }) {
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{title}</h3>
      <div className="flex flex-wrap gap-1.5">
        {terms.map((t) => (
          <Badge key={t} variant="outline" className="font-normal">
            {t}
          </Badge>
        ))}
      </div>
    </section>
  )
}
