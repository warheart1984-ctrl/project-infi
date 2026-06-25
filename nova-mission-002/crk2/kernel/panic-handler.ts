export const panicHandler = {
  panic(reason: string): never {
    throw new Error(`CRK-2 kernel panic: ${reason}`);
  },

  recover(_error: unknown): { recovered: boolean; message: string } {
    return { recovered: false, message: "Fail-closed: manual forensics required" };
  },
};
