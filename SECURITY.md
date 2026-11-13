# Security and private configuration

Keep provider keys, bot tokens, proxy credentials, private signing/TLS keys, production configuration, exports and personal datasets outside Git. Only empty examples or synthetic fixtures belong in the repository. Existing author credits and third-party license notices must remain intact.

Before sharing a reproduction, remove authorization headers, cookies, private endpoints and personal records from logs and attachments. Use the smallest synthetic example that demonstrates the problem.

The secret-scan workflow runs pinned Gitleaks against current files and incoming commits. It redacts detected values, ignores no project-defined suppression comments, and does not require provider credentials. It does not prove that an exposed key has been revoked.

If a real credential was committed, rotate or revoke it in its owning service, check dependent deployments, and review the affected history, branches, tags and releases. Do not paste its value into an issue. Coordinate any history rewrite with repository users before a force push. See [GitHub's sensitive-data removal guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
