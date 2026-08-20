# Provider Framework

Every external integration implements `BaseProvider` and registers with `ProviderRegistry`.

A provider supplies:

- a stable descriptor and capability list;
- safe configuration validation;
- optional live health checks;
- provider-specific operations through a client derived from `ProviderClient`.

`ProviderClient` centralizes:

- async HTTP requests;
- timeout behavior;
- limited retries with backoff;
- correlation IDs;
- safe structured logging;
- consistent error translation.

Secrets, authorization headers, request bodies containing credentials, and raw tokens must never be logged or rendered.
