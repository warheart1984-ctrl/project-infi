import { ULXValidator } from '@aaes-os/ulx-governance';

export interface ULXVirtualMachineResult {
  accepted: boolean;
  bytecode: string;
}

export class ULXVirtualMachine {
  private readonly validator = new ULXValidator();

  run(bytecode: string): ULXVirtualMachineResult {
    const validation = this.validator.validate(bytecode);
    return {
      accepted: validation.passed,
      bytecode,
    };
  }
}
