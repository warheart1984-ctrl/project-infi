From Coq Require Import Bool.
Require Import Types.

Parameter OIWL_Sense : TrajectoryMessage -> OIWL_Report.
Parameter Forge_k_Project : TrajectoryMessage -> OIWL_Report -> InvariantObject.
Parameter Eval_LiSCAL : InvariantObject -> AxisResult.
Parameter Eval_EGL : InvariantObject -> AxisResult.
Parameter Eval_SDAF : InvariantObject -> AxisResult.
Parameter Eval_SSAGL : InvariantObject -> AxisResult.
Parameter Stable : InvariantObject -> bool.
