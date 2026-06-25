export function consensus<T>(plans: T[]): T {
  return plans[0] as T;
}
