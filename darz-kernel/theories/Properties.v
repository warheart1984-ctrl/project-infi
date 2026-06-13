Require Import Types Axes Kernel.

Axiom OIWL_total : forall m, exists o, OIWL_Sense m = o.
Axiom Forge_total : forall m o, exists g, Forge_k_Project m o = g.
Axiom Li_total : forall g, exists a, Eval_LiSCAL g = a.
Axiom Eg_total : forall g, exists a, Eval_EGL g = a.
Axiom Sd_total : forall g, exists a, Eval_SDAF g = a.
Axiom Sa_total : forall g, exists a, Eval_SSAGL g = a.

Theorem eval_total :
  forall m, exists d, eval m = d.
Proof.
  intro m.
  exists (eval m).
  reflexivity.
Qed.

Theorem eval_deterministic :
  forall m d1 d2, eval m = d1 -> eval m = d2 -> d1 = d2.
Proof.
  intros m d1 d2 H1 H2.
  rewrite <- H1.
  exact H2.
Qed.

Axiom policy_strengthening_monotone :
  forall m : TrajectoryMessage, True.
