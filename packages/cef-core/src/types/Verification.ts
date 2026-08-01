export type VerificationResult = 'passed' | 'failed' | 'pending' | 'waived';

export type VerificationCheck = {
  id: string;
  result: VerificationResult;
};

export type CefVerification = {
  checks?: VerificationCheck[];
};
