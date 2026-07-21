export interface ULXValidationResult {
  passed: boolean;
  severity: 'info' | 'warn' | 'error' | 'fatal';
  message: string;
  canonicalBytecode?: string;
}

export class ULXValidator {
  validate(bytecode: string): ULXValidationResult {
    if (!bytecode.trim()) {
      return {
        passed: false,
        severity: 'error',
        message: 'ULX bytecode must not be empty',
      };
    }

    if (!bytecode.startsWith('ULX::')) {
      return {
        passed: false,
        severity: 'fatal',
        message: 'ULX bytecode must be constitutionalized before execution',
      };
    }

    return {
      passed: true,
      severity: 'info',
      message: 'ULX bytecode is valid',
      canonicalBytecode: bytecode,
    };
  }
}
