# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in AAES-OS, please report it responsibly.

**Do NOT** open a public issue for security vulnerabilities.

Instead, please send an email to: security@example.com

Include:
- A description of the vulnerability
- Steps to reproduce the issue
- Any potential impact or exploit scenarios

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.0 | ✅ |
| < 0.2.0 | ❌ |

## Security Principles

AAES-OS is designed with governance and observability at its core:

1. **RunLedger**: All runs and spans are recorded in an immutable ledger
2. **TraceBus**: All trace events are published and can be audited
3. **Invariant Engine**: System invariants are enforced at runtime
4. **Fault Journal**: Fault patterns are tracked for analysis

## Known Security Considerations

- **Ops Console**: The ops console exposes telemetry and metrics. Ensure proper access controls in production.
- **Prometheus**: Metrics endpoints should be secured and not exposed publicly.
- **Local Model Runtime**: When using local models (Ollama), ensure the model server is properly secured.

## Dependency Security

We regularly update dependencies to address known vulnerabilities. CI includes automated dependency scanning where available.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
