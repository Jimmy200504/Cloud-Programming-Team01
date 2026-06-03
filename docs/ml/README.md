# ML Spec Index

This directory is the source of truth for the ML branch.

All ML-owned code, config keys, docs, AWS resource aliases, and test fixtures should use the `ml`, `ml_`, `ml-`, or `ML_` prefix to avoid collisions during final integration.

## Documents

- [SPEC.md](SPEC.md): scope, architecture, ownership boundaries, and acceptance criteria.
- [CONTRACTS.md](CONTRACTS.md): JSON input/output contracts that HMI, Cloud, and Hardware teams can depend on.
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md): step-by-step execution plan for local Mac development and Raspberry Pi handoff.
- [TEST_PLAN.md](TEST_PLAN.md): unit, mock, integration, and Pi smoke test requirements.

## Development Rule

Do not implement a feature until its input, output, error cases, and acceptance criteria exist in this spec set.
