# Personalization Optimization

**Scenario ID:** `personalization`
**Category:** Personalization
**Simulated agents:** 200
**Simulated duration:** 48 hours (30-minute rounds)

## Business Context

Intercom's Automated Outbound Engine uses OpenAI to generate personalized emails, scoring each on a 0-100 scale via the same LLM that authored it. This creates a circular evaluation problem: the AI grades its own homework, and a "95-score" email may not actually outperform a "75-score" email with real recipients.

The current personalization workflow has several gaps:

- **Circular scoring** — The generating LLM's self-assessment doesn't correlate with real-world engagement
- **No pre-send validation** — There's no mechanism to test whether personalization actually drives engagement before hitting send
- **Segment blindness** — Different segments respond to different tones, but this is not validated before deployment
- **Rep capacity constraint** — Manual personalization targets are 25 emails per rep per week, so variant testing is impractical with live sends

## What the Simulation Tests

The simulation pits 10 email variants against 200 synthetic personas (100 per variant pair). Variants are systematically designed to isolate specific personalization dimensions:

| Variant | Tone | Length | Personalization Depth | CTA Style |
|---------|------|--------|-----------------------|-----------|
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

Each variant is tested against the same persona population, allowing direct comparison.

## Expected Insights

| Output | What It Tells You |
|--------|-------------------|
| Email variant ranking by simulated engagement | Which of the 10 variants produces the best predicted response rate |
| Most impactful personalization dimensions | Whether tone, length, personalization depth, or CTA style matters most |
| Segment-specific variant recommendations | The best variant for each industry/role combination |
| Tone effectiveness by persona type | How executives vs. directors respond to formal, casual, data-driven, etc. |
| CTA style conversion prediction | Whether soft asks, hard asks, or questions drive more replies by persona |

## How to Interpret Results

### Variant Rankings vs. LLM Scores

The key insight is the gap between what the generating LLM scored highly and what the simulation predicts will actually perform. If variant 9 (Urgency + Short + Pain-point-specific + Hard ask) was LLM-scored at 75 but simulation-ranked #1, that's a signal the LLM's scoring model is miscalibrated for that segment.

### Dimension Importance

The report breaks down which of the four dimensions (tone, length, personalization depth, CTA style) contributes most to engagement variance. If personalization depth explains 60% of the variance while tone only explains 10%, your team should invest in deeper personalization rather than tone-testing.

Typical patterns to look for:

- **Executives** often prefer short + data-driven + soft ask (they're time-constrained and resistant to hard sells)
- **Directors** tend to engage more with medium-length + role-specific content (they want details relevant to their function)
- **Technical personas** (IT Leaders) frequently respond better to consultative or challenge-framing tones

### Segment-Specific Recommendations

Don't use a single "best variant" across all segments. The segment matrix shows which variant wins for each industry/role pair. Healthcare CX Directors may respond to story-driven approaches, while Fintech IT Leaders prefer data-driven framing. Use these segment-specific winners in your outbound sequences.

### CTA Conversion Signals

A high reply rate to "question" CTAs doesn't always mean higher conversion — it may indicate curiosity without buying intent. Compare CTA reply rates alongside the sentiment of simulated replies (positive, neutral, negative) to identify which CTAs generate qualified interest.

## Running This Scenario

```bash
# Load the scenario
curl http://localhost:5001/api/gtm/scenarios/personalization

# Get just the seed text for the knowledge graph
curl http://localhost:5001/api/gtm/scenarios/personalization/seed-text

# View related seed data
curl http://localhost:5001/api/gtm/seed-data/email_templates
curl http://localhost:5001/api/gtm/seed-data/persona_templates
```

Or select **"Personalization Optimization"** from the Scenario Builder in the frontend.
