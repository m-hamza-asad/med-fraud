# Security and Limitations

Localhost binding, Argon2 password hashing, HTTP-only same-site cookies, CSRF validation on sensitive writes, generic login errors, extension/size checks, formula-safe CSV export, foreign keys, audit events, restrictive browser security headers, and aggregate-only profiling form the POC baseline. HTTPS is not used on localhost, so the cookie is not marked Secure. Use tokenized data only.

Authentication rate limiting, enterprise identity, encryption-at-rest key management, formal privacy impact assessment, and regulator/payer policy approval are outside this local POC. Generic contract fields generated from catalogue semantics must be confirmed against each payer's source mappings and policy owners before operational use. Synthetic labels and outcome columns are never evidence of performance or policy correctness.

