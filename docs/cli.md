# CLI Reference

```bash
platform-forge new gateway
platform-forge new gateway --interactive
platform-forge doctor
platform-forge version
```

Common gateway options:

```bash
platform-forge new gateway \
  --project-name ticket-platform \
  --domain ticketing \
  --providers ticketmaster,seatgeek,gametime \
  --services pricing,inventory,fulfillment \
  --frontend vite \
  --event-bus redis \
  --observability logfire
```

AI-assisted mode is optional:

```bash
platform-forge new gateway \
  --interactive \
  --from-description "Build a ticketing platform with provider inventory adapters"
```

When AI is not configured, Platform Forge uses the manual configuration gathered
from flags or prompts.
