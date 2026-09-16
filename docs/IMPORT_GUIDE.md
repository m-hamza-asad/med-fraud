# Import Guide

Download a template from `data/templates`: Shafafiya-aligned Excel, eClaimLink-aligned Excel, canonical Excel, or the canonical multi-CSV directory. The implemented intake accepts a `claim_header` sheet or a flat claim CSV with the columns shown in the template.

Choose the correct jurisdiction profile and analysis date. Validation checks extension, size, required columns, duplicate source keys/checksum, ISO dates, money, future service dates, and the rolling five-year window. Blocking errors write no claim rows; warnings remain visible. Formula cells are not evaluated and macro-enabled files are rejected by extension.

Optional datasets listed in `facts_json.available_datasets` enable family readiness. Missing data disables the affected executable rules and makes coverage Partial.

