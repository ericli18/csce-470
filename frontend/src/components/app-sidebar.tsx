import {
  Delete02Icon,
  InboxIcon,
  Moon02Icon,
  MoreHorizontalIcon,
  NotificationOff01Icon,
  PencilEdit02Icon,
  Search01Icon,
  StarIcon,
  Sun03Icon,
} from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar'
import { NewAlertDialog } from '@/components/new-alert-dialog'
import type { Inbox } from '@/lib/papers'

export type View = { kind: 'all' } | { kind: 'starred' } | { kind: 'alert'; id: number }

type Props = {
  inboxes: Inbox[]
  view: View
  onViewChange: (v: View) => void
  unread: (inbox: Inbox) => number
  totalUnread: number
  starredCount: number
  dark: boolean
  onToggleDark: () => void
  onCreateAlert: (query: string) => void
  onDeleteAlert: (id: number) => void
}

export function AppSidebar({
  inboxes,
  view,
  onViewChange,
  unread,
  totalUnread,
  starredCount,
  dark,
  onToggleDark,
  onCreateAlert,
  onDeleteAlert,
}: Props) {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center gap-2 px-1 py-1.5">
          <div className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <HugeiconsIcon icon={Search01Icon} className="size-4" strokeWidth={2.5} />
          </div>
          <span className="font-heading text-base font-semibold group-data-[collapsible=icon]:hidden">Alertr</span>
        </div>
        <NewAlertDialog onCreate={onCreateAlert} />
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  isActive={view.kind === 'all'}
                  onClick={() => onViewChange({ kind: 'all' })}
                  tooltip="All alerts"
                >
                  <HugeiconsIcon icon={InboxIcon} />
                  <span>All alerts</span>
                </SidebarMenuButton>
                {totalUnread > 0 && <SidebarMenuBadge>{totalUnread}</SidebarMenuBadge>}
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  isActive={view.kind === 'starred'}
                  onClick={() => onViewChange({ kind: 'starred' })}
                  tooltip="Starred"
                >
                  <HugeiconsIcon icon={StarIcon} />
                  <span>Starred</span>
                </SidebarMenuButton>
                {starredCount > 0 && (
                  <SidebarMenuBadge className="text-muted-foreground">{starredCount}</SidebarMenuBadge>
                )}
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Your alerts</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {inboxes.map((inbox) => {
                const n = unread(inbox)
                return (
                  <SidebarMenuItem key={inbox.id}>
                    <SidebarMenuButton
                      isActive={view.kind === 'alert' && view.id === inbox.id}
                      onClick={() => onViewChange({ kind: 'alert', id: inbox.id })}
                      tooltip={inbox.query}
                      className={n > 0 ? 'font-medium' : 'text-muted-foreground'}
                    >
                      <span
                        aria-hidden
                        className="flex size-4 shrink-0 items-center justify-center rounded-md bg-sidebar-accent text-[10px] font-semibold text-sidebar-accent-foreground uppercase group-data-[collapsible=icon]:size-4"
                      >
                        {inbox.query.charAt(0)}
                      </span>
                      <span>{inbox.query}</span>
                    </SidebarMenuButton>
                    {n > 0 && (
                      <SidebarMenuBadge className="group-hover/menu-item:opacity-0 group-has-aria-expanded/menu-item:opacity-0">
                        {n}
                      </SidebarMenuBadge>
                    )}
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        render={<SidebarMenuAction showOnHover aria-label={`Options for ${inbox.query}`} />}
                      >
                        <HugeiconsIcon icon={MoreHorizontalIcon} />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent side="right" align="start" className="w-44">
                        <DropdownMenuItem disabled>
                          <HugeiconsIcon icon={PencilEdit02Icon} />
                          Edit query
                        </DropdownMenuItem>
                        <DropdownMenuItem disabled>
                          <HugeiconsIcon icon={NotificationOff01Icon} />
                          Mute
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem variant="destructive" onClick={() => onDeleteAlert(inbox.id)}>
                          <HugeiconsIcon icon={Delete02Icon} />
                          Delete alert
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div className="flex justify-end px-1 group-data-[collapsible=icon]:justify-center">
          <Button variant="ghost" size="icon-sm" onClick={onToggleDark} aria-label="Toggle dark mode">
            <HugeiconsIcon icon={dark ? Sun03Icon : Moon02Icon} />
          </Button>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
