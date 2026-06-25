import type {
  AAESRequest,
  AAESStep,
  AaesError,
  ReconstructedSpan,
} from "./types.js";

/** POST /aaes/execute request body — interface §10.1 */
export type AAESExecuteRequestBody = AAESRequest;

export type AAESExecuteResponse =
  | {
      ok: true;
      trace_id: string;
      span_id: string;
      state: string;
      result: Record<string, unknown>;
      steps: AAESStep[];
    }
  | {
      ok: false;
      trace_id: string;
      error: AaesError;
    };

export type AAESTraceResponse =
  | {
      ok: true;
      reconstructed: ReconstructedSpan;
    }
  | {
      ok: false;
      error: AaesError;
    };

export interface AaesHttpHandlers {
  postExecute(body: AAESExecuteRequestBody): Promise<AAESExecuteResponse>;
  getTrace(trace_id: string): Promise<AAESTraceResponse>;
}

export class AaesApiStub implements AaesHttpHandlers {
  async postExecute(body: AAESExecuteRequestBody): Promise<AAESExecuteResponse> {
    return {
      ok: false,
      trace_id: body.trace_id,
      error: { code: "AAES_NOT_IMPLEMENTED", message: "POST /aaes/execute not implemented" },
    };
  }

  async getTrace(_trace_id: string): Promise<AAESTraceResponse> {
    return {
      ok: false,
      error: { code: "AAES_NOT_IMPLEMENTED", message: "GET /aaes/trace/{trace_id} not implemented" },
    };
  }
}
