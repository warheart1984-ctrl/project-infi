import type { ULS } from "./types.js";
import { notImplemented } from "./error.js";

export class UlsStub implements ULS {
  readonly surface_id = "uls.v1.stub";

  normalize(_raw: string | Record<string, unknown>) {
    return notImplemented<Record<string, unknown>>("ULS.normalize");
  }
}
