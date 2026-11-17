import { useState } from 'react'
import { PlusSignIcon } from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'

const EXAMPLES = [
  'vitamin d and depression',
  'how to prevent kidney stones',
  'screen time and kids mental health',
  'gum disease and heart disease',
]

export function NewAlertDialog({ onCreate }: { onCreate: (query: string) => void }) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const trimmed = query.trim()

  function submit() {
    if (!trimmed) return
    onCreate(trimmed)
    setQuery('')
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button className="w-full group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:p-0" />
        }
      >
        <HugeiconsIcon icon={PlusSignIcon} strokeWidth={2.5} />
        <span className="group-data-[collapsible=icon]:hidden">New alert</span>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>New alert</DialogTitle>
        </DialogHeader>
        <form
          className="grid gap-3"
          onSubmit={(e) => {
            e.preventDefault()
            submit()
          }}
        >
          <Textarea
            aria-label="Alert query"
            autoFocus
            rows={3}
            placeholder="e.g. does magnesium help with migraines"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                submit()
              }
            }}
          />
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLES.map((ex) => (
              <Badge key={ex} variant="outline" render={<button type="button" onClick={() => setQuery(ex)} />}>
                {ex}
              </Badge>
            ))}
          </div>
          <DialogFooter className="pt-2">
            <DialogClose render={<Button type="button" variant="ghost" />}>Cancel</DialogClose>
            <Button type="submit" disabled={!trimmed}>
              Create alert
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
