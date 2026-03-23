# Personalization Optimization

**ID:** `personalization` | **Category:** Personalization | **API:** `GET /api/gtm/scenarios/personalization`

## Business Context

Intercom's Automated Outbound Engine uses OpenAI to generate personalized emails, scoring them 0–100 based on the generating LLM's own self-assessment. This creates a circular quality problem: the same model that writes the email also judges it. A "95-score" email may not outperform a "75-score" email with real recipients.

There's no mechanism to validate whether personalization actually drives engagement before sending. Different customer segments respond to different tones and levels of personalization, but this is never tested — reps are manually producing ~25 emails per week with no systematic variant testing.

This scenario breaks the feedback loop by testing 10 email variants against 100 synthetic personas each, ranking them by **simulated recipient behavior** rather than generator self-assessment.

## What the Simulation Tests

The simulation generates **200 synthetic agents** and exposes each to multiple email variants, measuring predicted response behavior.

### Email Variants (10 total)

Each variant differs across four personalization dimensions:

| # | Tone | Length | Personalization Depth | CTA Style |
|---|------|--------|-----------------------|-----------|
| 1 | Formal | Short | Company-only | Soft ask |
| 2 | Formal | Medium | Role-specific | Hard ask |
| 3 | Casual | Short | Pain-point-specific | Question |
| 4 | Casual | Medium | Company-only | Soft ask |
| 5 | Data-driven | Short | Role-specific | Hard ask |
| 6 | Story-driven | Medium | Pain-point-specific | Soft ask |
| 7 | Challenge-framing | Short | Company-only | Question |
| 8 | Social-proof | Medium | Role-specific | Soft ask |
| 9 | Urgency | Short | Pain-point-specific | Hard ask |
| 10 | Consultative | Long | Role-specific | Question |

### Target Personas
- VP of Support
- CX Director
- IT Leader
- Head of Operations

### Firmographic Distribution
- **Industries:** SaaS, Healthcare, Fintech, E-commerce
- **Company sizes:** 200–500, 500–1000, 1000–2000 employees

### Simulation Parameters
- **Duration:** 48 hours simulated time
- **Round interval:** 30 minutes
- **Mode:** Twitter (threaded discussion format — agents react publicly to variants, revealing reasoning)

## Expected Insights

1. **Email variant ranking by simulated engagement** — Ordered list of all 10 variants by predicted response rate
2. **Most impactful personalization dimensions** — Which of the four dimensions (tone, length, depth, CTA) moves the needle most
3. **Segment-specific variant recommendations** — Best variant per industry/company-size combination
4. **Tone effectiveness by persona type** — Which tone resonates with each role
5. **CTA style conversion prediction** — Soft ask vs hard ask vs question performance by segment

## How to Interpret Results

### Variant Rankings
The top-line ranking orders all 10 variants by aggregate engagement prediction. But the real value is in the **segment breakdown** — a variant that ranks #7 overall might be #1 for Healthcare IT Leaders. Always check segment-level results before picking a "winner."

### Personalization Dimension Impact
The report decomposes engagement into contribution from each dimension. Example output:

```
Dimension Impact (relative contribution to engagement):
  Personalization Depth: 38%
  Tone: 27%
  CTA Style: 22%
  Length: 13%
```

If one dimension dominates (>35%), focus optimization efforts there. If contributions are flat (~25% each), the segment is responding to overall message quality rather than any single factor.

### Segment-Specific Recommendations
Cross-reference the variant matrix with segment results. Common patterns to look for:
- **Enterprise/Healthcare** tends to prefer formal tone + role-specific personalization
- **SMB/SaaS** often responds better to casual tone + pain-point-specific content
- **IT Leaders** across all segments typically favor data-driven or consultative approaches

These patterns will be specific to the simulation run — use them as hypotheses to validate, not absolute rules.

### CTA Effectiveness
CTA style interacts strongly with persona seniority:
- **Executives** (VP-level): Questions and soft asks outperform hard asks
- **Directors**: Mixed — depends on tone pairing
- **Managers**: Hard asks with clear next steps often perform best

Look for CTA × persona interactions in the report rather than treating CTA effectiveness as a single number.

### Twitter Mode Note
This scenario uses "twitter" simulation mode, meaning agents discuss and react to variants in a threaded format. This provides qualitative insight alongside quantitative rankings — check the conversation threads for **why** agents preferred certain variants. The reasoning often reveals actionable messaging insights that raw numbers miss.
