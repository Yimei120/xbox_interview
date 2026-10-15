# Data and analysis audit

Audit date: 2026-10-15. Read-only review of the source CSV and current presentation metrics. The source CSV and presentation were not changed. No dataset generation was performed.

## Data integrity

- The source CSV matches the current repository byte for byte. SHA-256: 2efe179b13bd3dba1cbc6817e40395db4f544f76807f82001156c1d0da686067.
- 7,970 rows, 300 unique players, five cohorts of 60, observed dates March 3–May 5, 2025, relative days 0–59.
- No missing fields, duplicate player-days, inconsistent signup dates, invalid dates/calendar flags, invalid plan/status values, negative counts, or plan-limit violations found.
- Every player has a day-0 row. Plan histories only stay unchanged or move Free to Paid. Cancellation records are Paid and final, with no subsequent activity.
- Two applicable repository consistency tests passed: cohorts/activity days and plans/status/limits. The seeded regeneration test was deliberately not run because no data generation was requested.
- 10,030 possible player-days have no row. Absence represents no observed activity, not an explicit cancellation. 198 players have a last observed day before day 59 without an explicit cancellation; their billing outcome cannot be inferred from disappearance.

## Slide metric reconciliation

All current headline metrics reconcile to an independent CSV calculation.

| Metric | Lower first-week attempts, ≤76 | Higher first-week attempts, ≥77 |
| --- | --- | --- |
| Retention, any activity days 28–34 | 73/151 = 48.3% | 107/149 = 71.8% |
| Conversion, days 7–59 among initially Free | 11/118 = 9.3% | 22/114 = 19.3% |

Median cutoff is 76 attempts, including success and error interactions, keeping ties together. It is a descriptive split, not an established product activation threshold. First-week measurement uses days 0–6 and precedes all observed conversions, so these exposures contain no post-upgrade behavior. The full retention comparison includes initially Paid users; restricting to initially Free users preserves the pattern: 47.5% versus 70.2%.

All acquisition, conversion, and cancellation counts also reconcile: 232 initially Free, 68 initially Paid, 33 upgrades, and 16 explicitly cancelled out of 101 ever-Paid players.

## Material interpretation issues

### 1. Day 7 is the first observed event, not a validated turning point

Exactly one player upgrades on day 7. Eleven upgrades occur on days 7–13, one-third of all 33. The cohort-based weekly rate of 11/232 = 4.74% is correctly calculated, and the chart is numerically correct. However, it estimates observed conversion among all not-yet-upgraded cohort members, including inactive users, rather than conversion probability per active opportunity.

Sensitivity using observed active player-days before upgrade, including the upgrade day:

| Window | Upgrades | Active opportunities | Upgrades per 100 active opportunities |
| --- | --- | --- | --- |
| Days 7–13 | 11 | 857 | 1.28 |
| Days 14–20 | 5 | 731 | 0.68 |
| Days 21–27 | 2 | 672 | 0.30 |
| Days 28–34 | 5 | 553 | 0.90 |
| Days 35–41 | 5 | 480 | 1.04 |
| Days 42–45 | 5 | 234 | 2.14 |

The last window is only four days. These rates are descriptive with few events and repeated opportunities per player. They do not prove a later optimum either. They show that more conversions in week two does not establish the highest per-active-opportunity propensity. Earlier windows contain more active opportunities. The weekly confidence intervals also overlap.

Source-code inspection reveals that the synthetic generator only permits upgrades on days 4–45. It does not impose a special day-7 trigger. The observed first event on day 7 can reflect random variation within this imposed window. The early and late boundaries therefore cannot identify natural real-world timing.

Recommended framing: “Upgrades first appear on day 7 in this sample. Test prompts starting then against a randomized holdout.” Avoid “day 7 is the proven turning point” or “optimal prompt timing.” A prompt-versus-holdout experiment tests that policy's incremental impact; an early-versus-later timing arm is needed to compare timing policies.

### 2. AI attempts partly measure underlying engagement

The source generator assigns an unobserved engagement category that influences active attendance, stopping, AI volume, and upgrade probability. Specific AI successes and errors are not causal inputs into the upgrade or stopping probabilities. Errors are random draws with feature-specific probabilities. Thus the generated correlation is compatible with a shared underlying cause by construction, and the error analysis cannot recover a simulated causal error effect that was never included.

Observed active-day sensitivity is consistent with that limitation. Among users active 6–7 days in the first week, conversion is 20.0% (2/10) for lower attempts and 21.1% (16/76) for higher attempts, much closer than the full-sample 9.3% versus 19.3% contrast. Among those active 4–5 days, the rates are 12.2% (6/49) versus 16.2% (6/37). Groups are small and unbalanced; these comparisons demonstrate confounding concerns, not complete removal of selection bias. Logistic adjustments provide complementary associative checks, not causal identification.

Recommended framing: “First-week AI activity is an early engagement proxy associated with later conversion and retention.” Do not claim that increasing attempt count will produce the observed percentage-point differences. Any feature-specific associations are exploratory, with only 33 conversion events and multiple comparisons.

### 3. Proposed experiment has a narrower causal estimand than total AI impact

Keeping AI access in all groups while randomizing guided onboarding and prompts measures the incremental effects of guidance and prompts. It does not measure the total effect of offering AI features versus not offering AI. “Organic” must mean conversion under the explicit control experience, not AI-free conversion.

The existing CSV has no randomized assignment, prompt exposure, acquisition channel, pre-existing purchase intent, or detailed task-value signal. It also records end-of-day plan status, limiting interpretation of upgrade-day event ordering. It supports a sensible experiment proposal, not attribution of existing conversions to AI.

## Recommended use

Keep the slide metrics. Present the group differences as descriptive early signals, describe day 7 as observed onset and a candidate test policy, and prioritize randomized incrementality measurement. The current presentation already notes synthetic data and the distinction between association and causal lift. This audit identifies reasons to keep those caveats explicit, without changing the slides in this read-only review.

## Evidence

- Source: https://github.com/vejadu/InterviewCase-Gaming-PC-App
- Unchanged input: ../data/raw/contoso_gaming_pc_app_output.csv
- Independent audit: ../analysis/audit_data.py
- Machine-readable reconciliation: data_audit.json
- Reference generator inspected only: source_generator_reference.py
- Repository validation tests inspected: source_test_dataset.py
