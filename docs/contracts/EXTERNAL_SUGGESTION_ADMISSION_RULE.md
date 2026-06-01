# External Suggestion Admission Rule

## Purpose

This file defines the project-wide law for handling external suggestions,
outside proposals, and imported architectural ideas.

External suggestions may be useful for pressure, comparison, or inspiration.

They do not enter AAIS as truth on arrival.

Project law decides whether they are admitted.

## Core Rule

External suggestions may be used for pressure, comparison, or inspiration,
but they do not enter the system directly.

All external proposals must pass through the project law filter before
adoption.

## Freeform Conversation Law

External proposals appearing in ordinary conversation are not implementation
truth.

Freeform turns may discuss, compare, critique, summarize, pressure-test, or
extract ideas from outside proposals without admission.

If a freeform turn crosses into adoption intent, the system must fail closed
unless admitted-form handling occurs first.

Suggestion is not truth.

Conversation is not admission.

Law decides entry.

## ARIS Non-Copy Clause

The active ARIS rule that sharpens this contract is:

> Raw outside proposals and private runs stay local.
> Only admitted, abstracted, or signature-only forms may move forward.

That means:

- outside ideas may be discussed, compared, critiqued, or pressure-tested
- raw outside wording must not be copied directly into architecture or shared
  truth
- adoption must use the documented admitted form, not the raw proposal text

## Admission Flow

1. suggestion received
2. law filter applied
3. doctrine violations removed
4. admissible form extracted
5. admitted form documented
6. only then may implementation begin

## Enforcement

External suggestions must not be treated as architectural truth on arrival.

They may not be adopted if they:

- violate project law
- collapse module boundaries
- introduce hidden authority
- move decision power into expression layers
- rely on heuristic inference where governed truth is required
- bypass documentation requirements

## Admissible Use

External input may be accepted only when it survives filtering in a form that:

- preserves doctrine
- respects module purpose
- remains testable
- remains documentable
- does not create new seams

## Documentation Law

Any external suggestion admitted after filtering must be documented as admitted
form.

Suggestion is not truth.

Law decides admission.

Admitted form becomes documented system truth.

## Runtime Hook

The shared runtime law surface for this rule is `src/project_infi_law.py`.

Project Infi law may observe external suggestions without adopting them.

If a caller marks an external suggestion for adoption, the runtime must fail
closed unless:

- the law filter is marked as applied
- the admitted form is documented

This keeps external comparison separate from architectural admission.

## Folder Inheritance Rule

All project-owned folder entry docs should inherit this law explicitly.

That means launcher, shell, runtime, frontend, mobile, training, evaluation,
service, test, and documentation folders may reference outside proposals
without treating them as admitted system truth.

Folder-local discussion does not create architectural admission.
