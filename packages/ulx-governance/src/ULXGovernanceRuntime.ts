import { TriCoreBus } from '@aaes-os/tri-core-protocol';

import { ConstitutionalCompiler } from './ConstitutionalCompiler.js';
import { BytecodeTracerHook } from './BytecodeTracerHook.js';
import { ULXValidator } from './ULXValidator.js';

export interface ULXGovernanceRuntimeOptions {
  bus?: TriCoreBus;
}

export interface ULXExecutionResult {
  source: string;
  bytecode: string;
  verified: boolean;
}

export class ULXGovernanceRuntime {
  private readonly compiler = new ConstitutionalCompiler();
  private readonly validator = new ULXValidator();
  private readonly tracer: BytecodeTracerHook;

  constructor(options: ULXGovernanceRuntimeOptions = {}) {
    this.tracer = new BytecodeTracerHook({ bus: options.bus });
  }

  execute(source: string): ULXExecutionResult {
    const bytecode = this.compiler.compile(source);
    const validation = this.validator.validate(bytecode);
    this.tracer.trace(source, bytecode, {
      validation: validation.message,
      passed: validation.passed,
    });

    return {
      source,
      bytecode,
      verified: validation.passed,
    };
  }
}
