export interface EnvelopeValidationResult {
  ok: boolean
  violations: string[]
}

export interface EnvelopeValidatorDeps {
  ucr: any // UcrEngine
  ala: any // AlaRuntime
  safety: any // SafetyRuntime
}
