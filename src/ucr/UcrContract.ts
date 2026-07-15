export class UcrEngine {
  evaluate(proposal: any, contract: any) {
    const reasons: string[] = []

    if (proposal.goal !== contract.goal) {
      reasons.push('Goal mismatch')
    }

    for (const op of proposal.operations) {
      if (!contract.allowedOps.includes(op.type)) {
        reasons.push(`Operation not allowed: ${op.type}`)
      }
      if (!contract.authorizedFiles.includes(op.file)) {
        reasons.push(`Unauthorized file: ${op.file}`)
      }
    }

    return { ok: reasons.length === 0, reasons }
  }
}
