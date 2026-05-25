---
slug: read-the-map
title: How to read the TideGuard map
order: 4
xp: 50
lang: en
grade: 6-8
sdgs: [14,13,4]
---

## What you see

When you open the **/map** page, you see:

- A satellite + ocean basemap (from MapTiler/OpenStreetMap).
- A semi-transparent **heatmap layer** showing predicted debris concentration.
- A **time slider** that lets you scroll from D+0 (today) to D+13 (two weeks ahead).
- A **legend** with low → high color scale.

## How to interpret a hotspot

A *hotspot* is a region where the model predicts unusually high concentration. It usually means one of three things:

1. **Convergence zone**: currents are bringing in debris from multiple directions.
2. **River outflow**: a rain event recently flushed urban litter to the coast.
3. **Pre-existing patch**: yesterday's hotspot drifting along the prevailing current.

## How to use it for action

1. Look at D+0 to see current hotspots — these are the highest-priority cleanup targets *today*.
2. Slide to D+3 / D+7 to see where the patch will drift — this helps NGOs plan ahead.
3. Cross-reference with citizen reports (orange pins) to confirm predictions on the ground.

## Limitations to be honest about

- The model has uncertainty. A "low" prediction doesn't guarantee a clean beach.
- It is calibrated on the Taiwan Strait region first; other regions need more local data.
- It can't yet predict storm-driven surges in real time.

The dashboard is a **decision-support tool**, not an oracle. Use it alongside common sense and local knowledge.


```task
- 30-minute mini-task: pick one street, river or beach near you and walk it. Photograph any plastic item bigger than a coin, then log it via the TideGuard app.
- Goal: at least 5 reports with photo + GPS within 30 minutes.
- Wrap-up: write 2 sentences in your notebook describing what surprised you.
```

```json
[
  {
    "q": "What does the time slider control?",
    "options": ["Map zoom", "Forecast day (D+0 to D+13)", "Theme color", "Audio narration"],
    "correct": 1,
    "explain": "Sliding right shows the forecast for future days; left shows today (D+0)."
  },
  {
    "q": "A 'hotspot' on the map usually indicates:",
    "options": [
      "Hot weather",
      "Predicted high debris concentration",
      "Bad cellular signal",
      "A research vessel"
    ],
    "correct": 1,
    "explain": "Hotspots are regions where the PINN predicts a high concentration value C."
  },
  {
    "q": "Why might you check D+3 in the morning?",
    "options": [
      "Bored",
      "Plan a cleanup for the weekend in the right spot",
      "Update wallpaper",
      "Track sharks"
    ],
    "correct": 1,
    "explain": "Looking 3 days ahead lets organizers pre-position volunteers where debris will arrive."
  },
  {
    "q": "Why are citizen reports shown alongside predictions?",
    "options": [
      "Decoration",
      "Ground truth to validate the model",
      "To sell ads",
      "For aesthetic"
    ],
    "correct": 1,
    "explain": "Reports verify the model on the ground and feed the next training run."
  },
  {
    "q": "If the model says 'low' concentration, you should:",
    "options": [
      "Trust it 100% and never go",
      "Treat it as a probability — still inspect your local beach if you can",
      "Believe the opposite",
      "Ignore it forever"
    ],
    "correct": 1,
    "explain": "Predictions have uncertainty. Use the map to prioritize, but don't replace local knowledge."
  }
]
```
