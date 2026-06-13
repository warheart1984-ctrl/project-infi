Require Import Types Axes.

Parameter make_execution_receipt :
  InvariantObject -> AxisResult -> AxisResult -> AxisResult -> AxisResult -> ExecutionReceipt.

Parameter make_block_receipt :
  InvariantObject -> AxisResult -> AxisResult -> AxisResult -> AxisResult -> BlockReceipt.

Definition eval (m : TrajectoryMessage) : ExecutionDecision :=
  let o := OIWL_Sense m in
  let g := Forge_k_Project m o in
  let aL := Eval_LiSCAL g in
  let aE := Eval_EGL g in
  let aS := Eval_SDAF g in
  let aA := Eval_SSAGL g in
  match Stable g, aL, aE, aS, aA with
  | true, Pass LiSCAL, Pass EGL, Pass SDAF, Pass SSAGL =>
      Execute (make_execution_receipt g aL aE aS aA)
  | _, _, _, _, _ =>
      Block (make_block_receipt g aL aE aS aA)
  end.
