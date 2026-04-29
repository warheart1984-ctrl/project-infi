# PROJECT LAWS

## 0. Purpose

These laws govern how all projects are built, modified, and maintained.
They are not suggestions. They are requirements.

---

## 1. Core Laws

### 1.1 One Job, One Purpose

Every module, system, and function must have a single clear responsibility.

### 1.2 Availability is Not Authority

Just because something exists does not mean it is allowed to act.

### 1.3 Nothing is Free

All actions must have cost, consequence, or trace.

### 1.4 If It Is Not Written Down, It Does Not Exist

Undocumented behavior is considered undefined and invalid.

---

## 2. Build Laws

### 2.1 Completion Definition

A task is complete only when:

* Code is implemented
* Tests pass
* Documentation is written

All three are required.

---

### 2.2 No Silent Changes

Every change must:

* be recorded
* be explained
* include why it was made

---

### 2.3 Bounded Scope

Each mission must:

* define scope clearly
* avoid expanding beyond that scope
* defer unrelated work

---

## 3. Runtime Laws

### 3.1 Explicit State

All critical runtime state must be explicit, not implied.

### 3.2 No Uncontrolled Interaction

Systems must not interact unless explicitly allowed.

### 3.3 Guard Before Action

All actions must pass validation or enforcement before execution.

---

## 4. Documentation Laws

### 4.1 Mission Report Required

Every mission must produce a report documenting:

* what changed
* why
* what was verified

---

### 4.2 Build Log Required

All missions must append to a shared build log.

---

### 4.3 System Docs Updated

If behavior changes, relevant documentation must be updated.

---

## 5. Governance Laws

### 5.1 Present Intent Priority

Current input overrides stale or previous context.

### 5.2 Context is Advisory

Past context may inform, but must not control decisions.

### 5.3 Authority is Scoped

Modules may only act within their defined role.

---

## 6. Integrity Laws

### 6.1 No Cross-System Bleed

Systems must not leak behavior into other systems unless explicitly designed.

### 6.2 Clean Transitions

State changes must:

* preserve required data
* remove invalid state
* avoid contamination

---

## 7. Expansion Laws

### 7.1 Integrate, Don’t Bypass

New features must integrate into existing systems, not work around them.

### 7.2 Version With Intent

Breaking changes must:

* be documented
* include reason
* include migration or impact notes

---

## 8. Final Law

If a change violates these laws, it is not valid—regardless of whether it works.

The system must remain:

* understandable
* governed
* consistent

---

## Enforcement

All contributors (human or AI) must follow these laws.
No mission is complete unless these laws are satisfied.
All logs must be timestamped using ISO 8601 UTC.