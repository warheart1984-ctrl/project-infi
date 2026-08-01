export type PromotionDecision = 'approved' | 'rejected' | 'hold';

export type CefPromotion = {
  decision: PromotionDecision;
  signature?: string | null;
  timestamp?: string | null;
};
