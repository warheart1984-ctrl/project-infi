import { CloudUpload, Download, MessageSquare, Plus, Search, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuAction,
} from "@/components/ui/sidebar";
import { LazyImportDialog } from "@/components/lazy-import-dialog";
import type { Chat, ChatSearchResult } from "@shared/schema";
import { spiralModeEnabled } from "@/lib/spiral-mode";

interface AppSidebarProps {
  chats: Chat[];
  searchQuery: string;
  searchResults: ChatSearchResult[];
  currentChatId: string | null;
  onNewChat: () => void;
  onSearchQueryChange: (value: string) => void;
  onSelectChat: (chatId: string) => void;
  onDeleteChat: (chatId: string) => void;
  onClearAllChats: () => void;
  onExportAllChats: () => void;
  onExportCurrentChat?: () => void;
  onSaveCurrentTranscript?: () => void;
  isLoading?: boolean;
  isSearching?: boolean;
}

export function AppSidebar({
  chats,
  searchQuery,
  searchResults,
  currentChatId,
  onNewChat,
  onSearchQueryChange,
  onSelectChat,
  onDeleteChat,
  onClearAllChats,
  onExportAllChats,
  onExportCurrentChat,
  onSaveCurrentTranscript,
  isLoading,
  isSearching,
}: AppSidebarProps) {
  const sortedChats = [...chats].sort((a, b) => b.updatedAt - a.updatedAt);
  const isSearchActive = searchQuery.trim().length > 0;
  const newChatLabel = spiralModeEnabled ? "New Thread" : "New chat";

  return (
    <Sidebar>
      <SidebarHeader className="p-3">
        <div className="space-y-2">
          <Button
            onClick={onNewChat}
            className="w-full justify-start gap-2"
            variant="outline"
            data-testid="button-new-chat"
          >
            <Plus className="h-4 w-4" />
            {newChatLabel}
          </Button>

          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(e) => onSearchQueryChange(e.target.value)}
              placeholder="Search all chats"
              className="pl-8"
              data-testid="input-search-chats"
            />
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>{isSearchActive ? "Search Results" : "Conversations"}</SidebarGroupLabel>
          <SidebarGroupContent>
            {isSearchActive ? (
              isSearching ? (
                <div className="p-4 text-center text-muted-foreground text-sm">
                  Searching...
                </div>
              ) : searchResults.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground text-sm">
                  No matching messages
                </div>
              ) : (
                <SidebarMenu>
                  {searchResults.map((result) => (
                    <SidebarMenuItem key={`${result.chatId}-${result.messageId || "title"}-${result.matchedAt}`}>
                      <SidebarMenuButton
                        isActive={currentChatId === result.chatId}
                        onClick={() => onSelectChat(result.chatId)}
                        data-testid={`search-result-${result.chatId}`}
                        className="h-auto py-2"
                      >
                        <MessageSquare className="h-4 w-4 mt-0.5 shrink-0" />
                        <div className="min-w-0">
                          <div className="truncate text-sm font-medium">{result.chatTitle}</div>
                          <div className="truncate text-xs text-muted-foreground">{result.snippet}</div>
                        </div>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              )
            ) : isLoading ? (
              <div className="p-4 text-center text-muted-foreground text-sm">
                Loading chats...
              </div>
            ) : sortedChats.length === 0 ? (
              <div className="p-4 text-center text-muted-foreground text-sm">
                No conversations yet
              </div>
            ) : (
              <SidebarMenu>
                {sortedChats.map((chat) => (
                  <SidebarMenuItem key={chat.id}>
                    <SidebarMenuButton
                      isActive={currentChatId === chat.id}
                      onClick={() => onSelectChat(chat.id)}
                      data-testid={`chat-item-${chat.id}`}
                      className="pr-8"
                    >
                      <MessageSquare className="h-4 w-4" />
                      <span className="truncate">{chat.title}</span>
                    </SidebarMenuButton>
                    <SidebarMenuAction
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteChat(chat.id);
                      }}
                      data-testid={`button-delete-chat-${chat.id}`}
                      className="z-10 bg-background/50 hover:bg-background" 
                    >
                      <Trash2 className="h-4 w-4" />
                    </SidebarMenuAction>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            )}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-3 border-t border-border">
        <div className="space-y-2">
          <LazyImportDialog />
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-muted-foreground"
            onClick={onExportAllChats}
            data-testid="button-export-history"
          >
            <Download className="h-4 w-4" />
            Export all chats
          </Button>
          {typeof onExportCurrentChat === "function" && (
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start gap-2 text-muted-foreground"
              onClick={onExportCurrentChat}
              data-testid="button-export-current-chat"
            >
              <Download className="h-4 w-4" />
              Export current chat
            </Button>
          )}
          {typeof onSaveCurrentTranscript === "function" && (
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start gap-2 text-muted-foreground"
              onClick={onSaveCurrentTranscript}
              data-testid="button-save-current-transcript"
            >
              <CloudUpload className="h-4 w-4" />
              Save current transcript
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-muted-foreground hover:text-destructive"
            onClick={onClearAllChats}
            data-testid="button-clear-all-chats"
          >
            <Trash2 className="h-4 w-4" />
            Delete all chats
          </Button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
