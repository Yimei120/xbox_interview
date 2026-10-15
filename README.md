# Xbox subscription growth case

A focused analysis of the supplied synthetic Contoso Gaming PC App dataset, with a five-slide HTML presentation about early engagement, conversion timing, and incrementality experiments. The data are not actual Xbox customer data.

## View the presentation

Open [presentation/index.html](presentation/index.html) in a browser. It is self-contained and works offline. Use the presentation controls or arrow keys to navigate; select Notes for the technical explanations and source context. Browser printing supports a landscape slide layout.

The five slides cover:

1. Business problem, two insights, and recommendations.
2. Later retention and conversion among lower- and higher-usage first-week groups.
3. Observed conversion timing and a candidate day-7 prompt test.
4. Analysis approach and evaluation criteria.
5. Actions for data science and engineering, including data limitations.

## Findings and interpretation

Using a median split of first-week total AI attempts (days 0–6), higher-usage users have 71.8% versus 48.3% later retention and 19.3% versus 9.3% subsequent conversion. Retention means activity at least once on days 28–34. Conversion compares initially Free players over days 7–59. These are descriptive associations, not causal lift.

The first observed upgrade occurs on day 7, and 11 of 33 upgrades occur on days 7–13. This is a candidate policy to test, not proven optimal timing. The supplied generator restricts upgrades to days 4–45 and makes underlying engagement influence usage and upgrade probability.

The proposed experiment separates guided AI onboarding from additional upgrade prompts. Because all groups retain AI access, it estimates guidance and prompt effects rather than the total effect of AI availability.

See [the data audit](outputs/DATA_AUDIT.md) for independent metric reconciliation, consistency checks, and interpretation concerns.

## Reproduce the analysis

Use Python 3.12 or later. Only the correlation and regression checks require NumPy.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis/answer_questions.py
python analysis/additional_questions.py
python analysis/check_engagement.py
python analysis/correlations.py
python analysis/build_engagement_groups.py
python analysis/audit_data.py
```

The final audit command needs internet access to compare the unchanged local CSV against the current upstream CSV. No script in this workflow generates a replacement dataset. The reference generator is included for provenance and code inspection only; do not run it to reproduce this analysis.

The presentation is the final authored document. Analysis scripts write JSON results under `outputs/`; they do not automatically rebuild the slides.

## Files

- `data/raw/`: unchanged source CSV.
- `source/`: original case brief, license, and provenance.
- `analysis/`: metric calculations, exploratory checks, and independent audit.
- `outputs/`: computed results, audit, and supporting research notes. The earlier `key_findings.md` records the proposed story before the later audit; use `DATA_AUDIT.md` for the final caveats.
- `presentation/`: final HTML deck and supporting chart data.
- `PLAN.md`: initial project scope.

## Source and license

The dataset, case brief, and reference generator/tests come from [vejadu/InterviewCase-Gaming-PC-App](https://github.com/vejadu/InterviewCase-Gaming-PC-App), revision `d723165e32eea097828e159dadaa9c310ad37633`. Preserve the upstream [MIT license](source/LICENSE) when reusing those materials. See [source provenance](source/PROVENANCE.md) for the input checksum and file mapping.
