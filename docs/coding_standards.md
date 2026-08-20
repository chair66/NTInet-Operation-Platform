# NOP Coding Standards

- Keep provider API calls out of routers and templates.
- Prefer configuration over hard-coded environment values.
- Preserve organization isolation and least-privilege RBAC.
- Make provider reads safe and provider writes explicit and auditable.
- Add abstractions only when they remove real duplication.
- Keep NOP deployable as one FastAPI application unless scale requires otherwise.
- Never log secrets or expose raw provider credentials in errors.
