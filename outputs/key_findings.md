# Two proposed conclusions

## Engagement patterns identify users more likely to convert
First-week (days 0–6) attempts predict subsequent conversion among 232 initially Free players: odds ratio per doubling of attempts = 1.98, approximate 95% CI 1.08–3.63, after controlling for first-week active days. This is an association, not evidence that increasing attempts causes conversion.

Engagement confounds error counts. Per five additional first-week errors, unadjusted conversion odds ratio is 2.01 (1.32–3.07), versus 1.38 (0.70–2.72) controlling for active days and log2(attempts). Retention odds ratio changes from 1.86 (1.32–2.62) to 0.78 (0.48–1.28), additionally controlling for initial plan. Retention is any activity on days 28–34. These checks support measured engagement confounding, not identification of all selection mechanisms.

Error rates also have no clear negative association: adjusted odds ratio per +5 percentage points is 1.72 (0.85–3.48) for conversion and 1.07 (0.71–1.59) for retention. Feature-mix sensitivity gives 1.45 (0.70–3.00) and 0.98 (0.65–1.50), respectively. Estimates are imprecise; only 33 conversion events. The data neither demonstrate that errors harm outcomes nor that errors are harmless.

## Days 7–13 are a candidate prompt-test window
First observed upgrade: day 7. Days 7–13: 11 of all 33 upgrades, 4.74% of 232 players not yet upgraded at the window start. Wilson 95% CI 2.67–8.29%; intervals overlap later weeks. Median upgrade: day 24. These are days since signup, not seven active days.

Source generator inspection shows upgrades are only permitted on days 4–45, and are driven by a synthetic engagement category, not measured errors or feature caps. This is reference-code inspection only; no data was generated. Consequently neither the onset nor cessation of conversion establishes a natural lifecycle boundary or optimal prompt timing.

Recommendation: test an engagement-triggered prompt in days 7–13 against later timing and a holdout; evaluate incremental conversion with retention as a guardrail. The fact that converters reached caps does not establish cap exposure as a predictor without a comparable non-converter baseline.
