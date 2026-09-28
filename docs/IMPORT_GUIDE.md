# Import Guide

Download a template from `data/templates`: Shafafiya-aligned Excel, eClaimLink-aligned Excel, canonical Excel, or the canonical multi-CSV directory. The implemented intake accepts a `claim_header` sheet or a flat claim CSV with the columns shown in the template.

Choose the correct jurisdiction profile and analysis date. Validation checks extension, size, required columns, duplicate source keys/checksum, ISO dates, money, future service dates, and the rolling five-year window. Validation stores a normalized preview only. Blocking errors prevent commit; warnings remain visible. Explicit commit is transactional and idempotent. Formula cells are not evaluated and macro-enabled files are rejected by extension.

The repository fixture uses profile `synthetic_uae` and analysis date `2028-04-02`. Its dates are parsed as `DD/MM/YYYY`; `hospital_id`, `patient_id`, and `tpa` become provider, member, and network tokens. The AED headers are treated as source AED values without exchange-rate conversion. Synthetic outcome labels are held out. Approved-above-requested cases are retained as warnings because they are anomaly examples rather than parser failures.

Optional mapped datasets enable rule-specific readiness. Canonical facts retain dataset, field, source key, validity, and version lineage. `signals`, `fraud_label`, `fraud_confidence`, and synthetic scores are discarded and cannot drive evaluation. Missing data disables the affected executable rules and makes coverage Partial.

