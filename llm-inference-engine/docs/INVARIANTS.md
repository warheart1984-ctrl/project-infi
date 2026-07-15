# Invariants

The following invariants are non-negotiable hard constraints. Any code change that violates an invariant must be rejected regardless of performance benefit or engineering convenience.

## Numerical Correctness

**GPU backend output must match CPU reference output within 1e-3 absolute tolerance on all standard test cases.**

Correctness is the primary metric; speed is secondary. Any optimization that introduces numerical deviation beyond this tolerance is unacceptable.

## Single Weight Upload

**Model weights are uploaded to device memory (cl_mem / VkBuffer) exactly once at model load time.**

No weight re-upload during inference, between requests, or between tokens under any circumstances. All weight buffers must be allocated and populated during model initialization and remain resident for the lifetime of the model.

## Exhaustive Error Checking

**All OpenCL API calls are wrapped in the CHECK_CL macro. All Vulkan API calls check the returned VkResult.**

No error code is silently ignored anywhere in the codebase. Every API call must be checked and errors must be logged and handled appropriately.

## VRAM Budget

**Total GPU memory allocation must remain strictly below governance.vram_budget_mb (default 3500MB) at all times.**

This includes during peak allocation (one layer's weights + activation buffers simultaneously resident). The governance layer must reject any request that would exceed this budget.

## Request Logging

**Every inference request — successful, failed, or timed out — produces exactly one JSONL entry written to governance.log_path before the server returns a response.**

No request goes unlogged. The log entry must include all required fields: timestamp, node, backend, prompt_tokens, completion_tokens, latency_ms, temperature, status, error (if any), cpu_temp_c, vram_used_mb, and fallback flag.

## GCN Wavefront Alignment

**All OpenCL kernel local work group sizes are multiples of 64.**

- For 1D kernels: 64 or 128
- For 2D kernels: (8, 8) = 64

This constraint applies to every kernel without exception. This is required for optimal performance on AMD GCN architecture.

## GPU-Free Startup

**The binary must start successfully and pass --selftest even when no GPU hardware is present or GPU drivers are not installed.**

In this state, only the CPU backend is available. No crash, no hang, no undefined behavior. The server must gracefully handle GPU initialization failures and fall back to CPU-only operation.

## Token Limit Pre-enforcement

**The max_tokens governance limit is evaluated and enforced before the first token is generated.**

A request that exceeds the limit is rejected at the API boundary with HTTP 400, not truncated mid-generation. This prevents resource exhaustion from oversized requests.

## Network Isolation

**The server binds exclusively to 127.0.0.1.**

No outbound network connections are made by the engine process at any time. DNS lookups, HTTP calls, or socket connections to any address other than localhost are forbidden. This ensures air-gapped operation.

## Self-Test Independence

**The --selftest command must run to completion and return a deterministic exit code (0 = pass, 1 = fail) without a model file being loaded.**

Self-test kernels use hard-coded 4×4 matrices with known expected outputs. The self-test validates core tensor operations and kernel compilation without requiring external model files.

## Thermal Throttling

**When CPU temperature exceeds governance.thermal_throttle_c (default 85°C), max_concurrent is reduced to 1 for that request cycle.**

This prevents thermal runaway under sustained load. The thermal event must be logged to the request log.

## Fallback Behavior

**Any exception from GPU executor must trigger automatic CPU fallback.**

The GPU error must be logged, the request retried with CPU executor, and the response must include `"fallback": true` in the log entry. This ensures service availability even when GPU backends fail.

## Atomic Concurrency Control

**The active request counter must be atomic and thread-safe.**

Race conditions in concurrency checking are unacceptable. Use std::atomic or equivalent to ensure thread-safe increment/decrement operations.

## File Locking for Logs

**JSONL log writes must use file locking (flock) for concurrent write safety.**

Multiple threads or processes must not corrupt the log file. Each write must acquire an exclusive lock, write the entry, flush, and release the lock.

## Zero-Length Sequence Handling

**The system must handle zero-length sequences (empty input) without crashing.**

This edge case must return a valid empty response, not cause a segmentation fault or undefined behavior.

## Single-Token Sequence Handling

**The system must handle single-token sequences correctly.**

This edge case tests boundary conditions in attention mechanisms and layer normalization.

## Non-Multiple-of-64 Sequence Length

**The system must handle sequence lengths that are not multiples of 64.**

Padding and masking must correctly handle arbitrary sequence lengths without performance degradation or correctness issues.

## All-Zero Weights

**The system must handle all-zero weight matrices correctly.**

This tests numerical stability and prevents division-by-zero or NaN propagation in layer normalization and attention mechanisms.

## Identity Weights

**The system must handle identity weight matrices correctly.**

This tests that matrix multiplication preserves the input when weights are identity matrices.

## Large Input Values

**The system must handle large input values without numerical overflow or instability.**

This tests numerical stability of operations like softmax, layer normalization, and attention mechanisms.

## Deterministic Output

**With --seed parameter, generation must be deterministic and reproducible.**

Same prompt + same seed + same model must produce identical output byte-for-byte. This is critical for testing and debugging.

## Latency SLA

**Inference latency must stay within acceptable thresholds for the hardware.**

- CPU: 30,000ms for 7B model
- OpenCL: 5,000ms for 7B model
- Vulkan: 5,000ms for 7B model

Exceeding these thresholds should trigger warnings and monitoring alerts.

## Memory Leak Prevention

**No memory leaks in GPU or CPU allocations.**

All allocated buffers must be freed. Use valgrind or similar tools to verify. GPU memory must be released when model is unloaded.

## Thread Safety

**All shared state must be thread-safe.**

The governance layer, model weights, and request logging must handle concurrent access correctly. Use mutexes, atomic operations, or lock-free data structures as appropriate.

## Configuration Immutability

**Governance configuration cannot change after server startup.**

Parameters like max_concurrent, vram_budget_mb, and thermal_throttle_c must be set at initialization and remain constant. Runtime reconfiguration requires server restart.

## Audit Trail Completeness

**Every governance decision (accept/reject) must be logged with reason.**

When a request is rejected due to governance rules, the log entry must include the specific rule that was violated and the values that caused the violation.
