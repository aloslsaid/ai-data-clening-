# Security Policy

## Reporting a vulnerability

Do not publish credentials, private CSV files, or exploitable details in a public issue. Contact the maintainer privately through GitHub's security reporting feature when available.

## Safe operation

- Run the API on a trusted local network unless authentication and deployment controls are added.
- CSV files uploaded to the API are processed by the backend; do not upload confidential data to an untrusted host.
- Keep `.env` files, datasets, exports, and logs out of Git.
- Review automatic transformations before using a cleaned dataset for consequential decisions.
