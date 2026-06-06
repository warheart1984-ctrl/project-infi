# UGR Rail Credit Purchase Contract (v1.0)

Ledger-only Pay for Tokens path. No Stripe in pilot scope.

## Flow

1. Payment handled off-platform.
2. Admin records payment reference.
3. `POST /api/ugr/credits/purchase` with signed `purchase_receipt` mints `purchased_rail_credits`.
4. Purchased credits are non-transferable P2P.

## Request

```json
{
  "tenant_id": "tenant:acme",
  "operator_id": "op-1",
  "amount": 50,
  "payment_reference": "invoice-2026-001",
  "trace_id": "purchase-trace-1"
}
```

## Schema

`schemas/ugr_rail_credit_purchase_receipt.v1.json`

## Implementation

- `src/ugr/rewards/rail_credit_purchase.py`
- `src/ugr/rewards/purchase_receipt.py`
