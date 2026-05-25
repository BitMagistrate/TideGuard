---
slug: good-report
title: How to make a quality citizen report
order: 5
xp: 50
lang: en
grade: 6-8
sdgs: [14,4,17]
---

## A useful report has 5 ingredients

1. **A clear photo** taken at the debris site (not stock photos, not screenshots).
2. **Accurate GPS coordinates** — TideGuard reads them from your phone automatically.
3. **A severity rating (1-5)** — be honest:
   - 1 = a single piece of trash
   - 3 = a small patch
   - 5 = significant accumulation across a beach or coastal area
4. **A debris type** — bottles, nets, foam, mixed, etc.
5. **A timestamp** — also automatic.

## Best practices

- Take the photo in **landscape orientation**, with the horizon visible if possible. This helps automatic verification.
- Don't include identifiable people in the photo (privacy).
- Walk *to* the debris if safe, instead of zooming from far away.
- Submit while still at the location (the GPS is more accurate).

## What happens after you submit

- The report enters the **pending** queue.
- A moderator (a fellow volunteer or local NGO partner) reviews it.
- If approved, it shows up on the public map and contributes 10–20 XP to your profile.
- A subset of approved reports becomes training data for the next model retraining.

## What NOT to do

- Don't submit duplicates (two reports of the same trash within 50 meters).
- Don't submit photos of irrelevant scenes (e.g. urban garbage cans).
- Don't fabricate severity to climb the leaderboard. The community catches it.


```task
- 30-minute mini-task: pick one street, river or beach near you and walk it. Photograph any plastic item bigger than a coin, then log it via the TideGuard app.
- Goal: at least 5 reports with photo + GPS within 30 minutes.
- Wrap-up: write 2 sentences in your notebook describing what surprised you.
```

```json
[
  {
    "q": "Which is most important for a useful report?",
    "options": ["A funny caption", "A clear in-situ photo", "Many emojis", "A long story"],
    "correct": 1,
    "explain": "A clear photo at the debris location is the single most valuable piece of evidence."
  },
  {
    "q": "When should you submit a report?",
    "options": [
      "A week later from home",
      "While still at the location",
      "Only after asking permission",
      "Never"
    ],
    "correct": 1,
    "explain": "Submitting on-site means the GPS is accurate and the photo is verifiable."
  },
  {
    "q": "Severity '5' means:",
    "options": [
      "1 piece of plastic",
      "A small bag",
      "Major accumulation along a beach",
      "Nothing"
    ],
    "correct": 2,
    "explain": "5 is reserved for visible large-scale accumulation, not single items."
  },
  {
    "q": "What's a privacy rule for photos?",
    "options": [
      "Always include faces",
      "Avoid identifiable people",
      "Use selfies",
      "Show car license plates"
    ],
    "correct": 1,
    "explain": "Avoid identifiable bystanders to respect privacy."
  },
  {
    "q": "What happens after submission?",
    "options": [
      "Nothing",
      "It goes to a moderator queue, gets approved/rejected, and contributes data + XP",
      "It is sent to all your friends",
      "Your phone is wiped"
    ],
    "correct": 1,
    "explain": "Reports are reviewed before going public on the map and contributing training data."
  }
]
```
