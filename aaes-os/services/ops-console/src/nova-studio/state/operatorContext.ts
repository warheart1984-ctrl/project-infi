import { createContext, createElement, useContext, type ReactNode } from 'react';

import type { OperatorContext } from './studioState.js';

const NovaOperatorContext = createContext<OperatorContext | null>(null);

export function OperatorContextProvider({
  children,
  value,
}: {
  children: ReactNode;
  value: OperatorContext;
}) {
  return createElement(NovaOperatorContext.Provider, { value }, children);
}

export function useOperatorContext(): OperatorContext {
  const context = useContext(NovaOperatorContext);
  if (!context) {
    throw new Error('Nova Studio operator context is missing');
  }
  return context;
}
