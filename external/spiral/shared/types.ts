export interface EchoTrace {
  matchedPromptId: string;
  matchedChatId?: string;
  score: number;
}

export interface HistoryReferenceSource {
  chatId: string;
  chatTitle: string;
}

export interface PromptMetadata {
  recurring: boolean;
  echoTrace?: EchoTrace;
  historySources?: HistoryReferenceSource[];
}
