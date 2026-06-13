Require Import Types.

Parameter replay_converges : InvariantObject -> Prop.

Definition stable_prop (ig : InvariantObject) : Prop :=
  replay_converges ig.

Axiom stable_bool_sound :
  forall ig, stable_prop ig -> True.
