export type PITBand = 1 | 2 | 3 | 4 | 5;

export interface PITContext {
  domain?: string;
  evidenceCount?: number;
}

export const pitEngine = {
  getBand(context: PITContext): PITBand {
    if ((context.evidenceCount ?? 0) >= 4) return 5;
    if ((context.evidenceCount ?? 0) >= 3) return 4;
    if (context.domain) return 3;
    return 1;
  },

  apply(band: PITBand, context: PITContext): PITBand {
    const next = this.getBand(context);
    return next >= band ? next : band;
  },
};
