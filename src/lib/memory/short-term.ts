import type { ChatMessage } from '@/lib/types/chat';

export interface ShortTermMemory {
  recentMessages: ChatMessage[];
  conversationSummary: string;
}

const MAX_RECENT_MESSAGES = 12;

export function buildShortTermMemory(messages: ChatMessage[]): ShortTermMemory {
  const recentMessages = messages.slice(-MAX_RECENT_MESSAGES);
  const olderMessages = messages.slice(0, -MAX_RECENT_MESSAGES);

  const conversationSummary =
    olderMessages.length === 0
      ? 'No previous summary yet.'
      : olderMessages
          .map((message) => `${message.role.toUpperCase()}: ${message.content}`)
          .join('\n')
          .slice(0, 1600);

  return {
    recentMessages,
    conversationSummary,
  };
}
