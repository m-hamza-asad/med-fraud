# User Guide

Sign in with a setup-configured account. The Overview reports the entire imported population as **Flagged**, **No flag detected**, or **Not evaluated**. An imported claim is never presented as clean before its batch has a completed evaluation run.

## Upload and evaluation

Open **Upload & validation** to choose a profile, analysis date, and `.csv` or `.xlsx` file. Validation creates a preview and does not write claims. Select **Commit validated rows** only after reviewing its errors and warnings. A committed batch then shows **Run evaluation**. Evaluation runs in the background across all 149 executable controls; the table displays progress, triggers, disabled controls, and failures. You can leave the page and return while it runs.

The `Synthetic UAE fixture` profile is the confirmed adapter for the supplied engineering fixture. Its currency is displayed as AED, but this label change is not a foreign-exchange conversion. Synthetic outcome labels remain excluded from evaluation.

## Claims and evidence

Claims are paginated so the entire imported list is accessible. **Not evaluated** directs the analyst back to the batch workflow. Claim detail now leads with a plain-language review reason, a labelled comparison with units, the amount boundary, coverage limitations and a concrete verification checklist. Technical rule IDs and formulas remain available under disclosure. A linked-event rule names the supporting earlier claim; if that record is unavailable, the screen labels the source indicator unverified and tells the analyst not to act on it without confirmation.

`No flag detected` is not a statement that fraud did not occur. `Partial` means an applicable executable control could not run because a required input was missing.

## Rule catalogue and threshold decisions

Open a rule to review its population, formula, required data, missing-data behavior, and parameter definitions. Each required field displays mapped-claim coverage plus a histogram or top-value summary from the committed dataset. Admin users can generate guidance only for parameters eligible for empirical support, simulate a candidate without mutation, and save an allowed value prospectively. Policy-owned and otherwise locked values explain why local editing is unavailable. Errors remain beside the affected parameter.

## Provider and network analysis

Provider pages show associated activity, support-aware peer context, a contribution trend, and linked claims. Network cards open a provider-to-member view inside the explicitly supplied network/TPA boundary. Ranked relationships explain why they appear; the optional graph and accessible table use the same claim-backed evidence. Source claim IDs, dates and amounts link to claim review. Full-population metrics remain separate from the bounded readable subset. An edge is not proof of coordination.

## Reports and audit

Reports export reconciled CSV, Excel, and PDF outputs. The Audit page is read-only. Every output retains the decision-support boundary: a signal is not a fraud finding and associated value is not confirmed exposure or savings.

