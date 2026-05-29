# Security Baseline Checklist

For platform-level controls and architecture decisions, use [`SECURITY.md`](./SECURITY.md).

This checklist is for quick operational verification:

1. Secrets are stored outside source control.
2. CI/CD identities use least privilege.
3. API endpoints enforce authorization and input validation.
4. TLS is enabled for all external traffic.
5. Audit logs are retained and queryable.
6. Incident response contacts and rotation runbooks are current.
