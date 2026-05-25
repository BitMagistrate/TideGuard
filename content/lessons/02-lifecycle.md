---
slug: lifecycle
title: The lifecycle of plastic in the ocean
order: 2
xp: 50
lang: en
grade: 6-8
sdgs: [14,12,13]
---

## From bottle to microplastic: the journey

Imagine a plastic water bottle dropped on a sidewalk near a river.

1. **Rain washes it into the river** within hours.
2. **The river carries it to the sea** in days.
3. **Currents and wind push it offshore**. Wind moves floating items ~3% of its own speed — that's the **windage coefficient (α)** in TideGuard.
4. **Diffusion (K)** spreads patches outward, making them larger but more diffuse.
5. **Beaching (λ)** — a fraction of plastic gets stranded on shorelines each day.
6. **UV + friction shred the bottle** into micro-fragments over months.
7. **Microplastic enters the food web**, eventually returning to humans.

## What slows the cycle?

- **Cleanups**: removing plastic at step 4-5 stops it from becoming microplastic.
- **Source reduction**: less single-use plastic = less input at step 1.
- **Prediction**: knowing *when* and *where* a hotspot will form lets us intervene at the right moment.

### The physics behind the forecast

TideGuard's PINN solves this equation:

> ∂C/∂t + ∇·((u_ocean + α·u_wind) · C) − ∇·(K · ∇C) + λ · C = S

- **C** is the concentration of debris at a point and time
- **u_ocean**, **u_wind** are velocity fields
- **α**, **K**, **λ** are the windage, diffusion and beaching parameters the model learns

You don't need calculus to use the app — but you should understand that the map you see is a *physical* prediction, not a guess.


```task
- 30-minute mini-task: pick one street, river or beach near you and walk it. Photograph any plastic item bigger than a coin, then log it via the TideGuard app.
- Goal: at least 5 reports with photo + GPS within 30 minutes.
- Wrap-up: write 2 sentences in your notebook describing what surprised you.
```

```json
[
  {
    "q": "How long does it typically take a piece of trash from a city to reach the open ocean?",
    "options": ["Several years", "Hours to days via rivers", "It never reaches it", "Only after recycling"],
    "correct": 1,
    "explain": "Storm drains and rivers transport urban litter to estuaries and the sea within hours to days."
  },
  {
    "q": "Which parameter describes how wind pushes floating debris?",
    "options": ["α (windage)", "K (diffusion)", "λ (beaching)", "C (concentration)"],
    "correct": 0,
    "explain": "α is the windage coefficient — typically ~3% of wind speed for a bottle, higher for items sticking out of the water."
  },
  {
    "q": "Beaching (λ) describes:",
    "options": [
      "Plastic floating offshore",
      "Plastic getting stuck on shorelines",
      "Plastic sinking",
      "Plastic eaten by fish"
    ],
    "correct": 1,
    "explain": "Beaching captures the rate at which floating debris gets trapped on beaches and shorelines."
  },
  {
    "q": "What is the BEST stage to intervene if you want to prevent microplastic formation?",
    "options": [
      "After it becomes microplastic",
      "While it's still a large, intact piece on the surface",
      "Once it's eaten by fish",
      "After it sinks to the seabed"
    ],
    "correct": 1,
    "explain": "Catching plastic while it is still a large floating item is dramatically more efficient than recovering microplastic later."
  },
  {
    "q": "What does the PINN actually predict?",
    "options": [
      "Exact pieces of plastic",
      "A field of debris concentration over space and time",
      "Wave heights only",
      "Fish populations"
    ],
    "correct": 1,
    "explain": "The model produces a continuous concentration field C(x,y,t) that maps to a heatmap on the dashboard."
  }
]
```
