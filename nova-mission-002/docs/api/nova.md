# Nova API (`nova.*`)

## `generateCode(input)`

Generate code with governance receipts.

```typescript
const result = await nova.generateCode({
  prompt: string,
  context?: CodeContext,
  constraints?: ConstraintSet,
});
// { code, receipts }
```

## `plan(input)`

Structured planning with invariant validation.

```typescript
const result = await nova.plan({ goal, context? });
// { plan, receipts }
```

## `refactor(input)`

```typescript
const result = await nova.refactor({ file, instructions });
```

## `verify(input)`

```typescript
const result = await nova.verify({ action });
```

## `applyPatch(input)`

```typescript
const result = await nova.applyPatch({ diff, reason });
```

## `explain(topic)`

Returns governed explanation with receipts.
