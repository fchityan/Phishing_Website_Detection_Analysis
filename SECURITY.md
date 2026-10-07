# Security Policy

Do not commit API keys, cloud credentials, private threat-intelligence feeds, customer browsing data, signed URLs, model-registry credentials, or production model artifacts.

Production deployments should:

- terminate TLS at an ingress or API gateway;
- set `REQUIRE_API_KEY=true`;
- store `API_KEY` and `MODEL_SHA256` in a secret manager;
- mount the promoted model read-only;
- run the service as non-root with no added Linux capabilities;
- protect `/metrics` at the network or gateway layer;
- apply rate and request-size limits;
- use dependency, secret, and container-image scanning;
- sign release images and verify provenance where supported;
- avoid logging raw URL/HTML feature payloads if they can contain sensitive browsing information.

If a credential is accidentally committed, revoke and rotate it before cleaning Git history.
