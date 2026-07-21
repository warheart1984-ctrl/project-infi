import { type MutationResult } from './MutationExecutor.types.js'
import { WorkspaceSnapshot } from './WorkspaceSnapshot.js'
import { SafetyRuntime } from '../safety/SafetyRuntime.js'

export class MutationExecutor {
  constructor(private safety: SafetyRuntime) {}

  execute(plan: any, proposal: any, contract: any, workspace: WorkspaceSnapshot): MutationResult {
    const applied: any[] = []
    const violations: string[] = []

    const clone = workspace.clone()

    for (const op of plan.normalized) {
      if (op.type === 'insert') {
        clone.setFile(op.file, op.content || '')
      }

      if (op.type === 'update') {
        clone.setFile(op.file, op.content || '')
      }

      if (op.type === 'delete') {
        clone.deleteFile(op.file)
      }

      applied.push(op)
    }

    const safetyResult = this.safety.check({ applied }, proposal, contract)

    if (!safetyResult.ok) {
      return {
        ok: false,
        applied: [],
        violations: safetyResult.violations,
      }
    }

    for (const op of applied) {
      if (op.type === 'insert' || op.type === 'update') {
        workspace.setFile(op.file, op.content || '')
      }
      if (op.type === 'delete') {
        workspace.deleteFile(op.file)
      }
    }

    return {
      ok: true,
      applied,
      violations,
    }
  }
}
