# Lawful Completion of a System

A system is not complete when it builds successfully.

A system is complete only when it has been verified, packaged into its declared distribution form, and proven to run correctly as a delivered artifact.

Completion requires:

- verified structure
- validated behavior
- generated distribution artifacts
- successful post-packaging execution

If any of these are missing, the system is not complete.

## Why It Matters

Build success is not the same thing as delivery truth. A source tree can compile while the shipped artifact still fails because an entry point is missing, assets were not packaged, configuration was not carried forward, or the delivered executable cannot boot outside the development environment.

Lawful completion matters because completion is a claim about the delivered system, not just the source.

## Project Infi Rule

Within Project Infi, completion is lawful only when the system can prove:

- what was verified
- what release form was generated
- what artifact now exists
- what post-packaging execution succeeded

This is why Build Lane and Shipping Lane are separate. Build produces output. Shipping proves completion.
