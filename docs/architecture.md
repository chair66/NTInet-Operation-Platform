# NOP Architecture

NOP is a single maintainable FastAPI application organized into three boundaries:

1. **Platform core** — authentication, organizations, RBAC, audit, notifications, configuration, and shared UI.
2. **Business modules** — LNP Management, NTI Mobile, DigiCloud, Reporting, and Administration.
3. **Provider integrations** — external API adapters such as Bandwidth and BrandVNO/OXIO.

Business modules must not implement provider authentication or raw HTTP requests. They call a provider method and work with normalized application data. Provider-owned data may be cached locally for resilience and operational visibility, but the external provider remains the source of truth.

NOP remains a modular monolith. Microservices, queues, and additional infrastructure should only be introduced when an actual operational requirement justifies them.
