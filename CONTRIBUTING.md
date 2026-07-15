# Contributing to AAES-OS

Thank you for your interest in contributing to AAES-OS!

## Constitutional Alignment

All contributions must comply with the **Unified Sovereign Specification v1.0.0** and **Prime Architect Constitutional Blueprint**:

- **Section 2.1.3 The Traceability Imperative** - All artifacts must have traceability links to constitutional clauses and UCDD standards
- **UCDD Standard S-002** - Traceability Linkage Protocol for all contributions
- **UCDD Standard S-003** - Version Sovereignty for all artifacts
- **UCDD Standard S-004** - Layered Authority requirements
- **UCDD Standard S-007** - AI Agent Compliance for AI-assisted contributions
- **Section 2.1.2 The Immutability Doctrine** - Constitutional artifacts are frozen

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone <repository-url>
   cd project-infi
   ```

2. **Install dependencies**
   ```bash
   pnpm install
   ```

3. **Build the project**
   ```bash
   pnpm build
   ```

4. **Run tests**
   ```bash
   pnpm test
   ```

## Code Style

- Follow existing TypeScript patterns
- Use the workspace structure properly
- Ensure all packages build successfully
- Add tests for new features
- **Include traceability links** in commit messages referencing UCDD standards and constitutional clauses
- **Follow constitutional freeze enforcement** - do not modify frozen constitutional artifacts

## Traceability Requirements (UCDD S-002)

All contributions must include traceability links:

- **Constitutional Clause References** (format: CONST-C\<nn\>)
- **UCDD Standard References** (format: UCDD-S\<nnn\>)
- **Requirement Register Entries** (format: REQ-\<TYPE\>\<nnnn\>)

Example commit message format:
```
feat: add new governance component

- UCDD-S004: Layered Authority compliance
- CONST-C01: Sovereignty principle
- REQ-ARCH-0001: Component catalog
```

## Submitting Changes

1. Create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them with traceability links
   ```bash
   git commit -m "feat: add your feature description

- UCDD-S002: Traceability linkage
- CONST-C02: Immutability doctrine
- REQ-IMPL-0001: Implementation requirement"
   ```

3. Ensure constitutional freeze is not violated
   ```bash
   python constitutional_freeze.py check
   ```

4. Push to your fork and create a pull request

## Constitutional Freeze Enforcement

The repository enforces constitutional freeze per Section 2.1.2:

- Git pre-commit hooks block modifications to frozen constitutional artifacts
- Violations generate Critical findings per UCDD S-005
- To modify constitutional artifacts, follow UCDD S-006 amendment procedure

## Package Structure

This is a pnpm workspace monorepo. When making changes:
- Check if your change affects multiple packages
- Run `pnpm build` to ensure all packages build
- Run `pnpm test` to run all tests
- Use workspace protocol for internal dependencies
- **Verify UCDD compliance** for all changes

## Authority Tiers (UCDD S-004)

Contributions are governed by layered authority:

- **PRIME** - Constitutional amendments, freeze/unfreeze operations
- **SOVEREIGN** - UCDD standard modifications, architectural decisions
- **DELEGATE** - Feature implementation, bug fixes
- **OBSERVER** - Read-only access, issue reporting

## Questions?

Open an issue or reach out to the maintainers.

## Constitutional References

- **Unified Sovereign Specification v1.0.0** - Section 2.1 Constitutional Foundations
- **UCDD Standards Bundle v1.2.0** - Standards S-002, S-003, S-004, S-005, S-006, S-007
- **Prime Architect Constitutional Blueprint** - Immutability Doctrine
