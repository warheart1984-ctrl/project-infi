From Coq Require Import List String Bool.
Import ListNotations.

Definition Hash256 := string.
Definition Reason := string.
Definition RegimeId := string.

Record TrajectoryMessage := {
  tm_id : Hash256;
  tm_origin : string;
  tm_lts_state : string;
  tm_history : string
}.

Record OIWL_Report := {
  drift_score : nat;
  entropy_delta : nat;
  contamination_flags : list string
}.

Record InvariantObject := {
  ig_id : Hash256;
  ig_class : string;
  ig_payload_hash : Hash256
}.

Inductive AxisName :=
  | K32 | LiSCAL | EGL | SDAF | SSAGL.

Inductive AxisResult :=
  | Pass (axis : AxisName)
  | Fail (axis : AxisName) (reasons : list Reason).

Record ExecutionReceipt := {
  er_invariant_id : Hash256;
  er_replay_hash : Hash256;
  er_regime_id : RegimeId
}.

Record BlockReceipt := {
  br_invariant_id : Hash256;
  br_failed_axes : list AxisName;
  br_reasons : list Reason;
  br_replay_hash : Hash256;
  br_regime_id : RegimeId
}.

Inductive ExecutionDecision :=
  | Execute (r : ExecutionReceipt)
  | Block (r : BlockReceipt).

Record ExecutionAudit := {
  audit_ig_id : Hash256;
  audit_stability : bool;
  audit_liscal : AxisResult;
  audit_egl : AxisResult;
  audit_sdaf : AxisResult;
  audit_ssagl : AxisResult;
  audit_decision : ExecutionDecision;
  audit_replay_hash : Hash256;
  audit_regime_id : RegimeId
}.
