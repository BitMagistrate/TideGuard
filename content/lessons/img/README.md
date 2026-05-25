# Lesson illustrations

This directory holds illustration assets referenced by lesson markdown files
(`content/lessons/*.md`). For the v0.x cycle of TideGuard, lessons embed
*conceptual* references rather than raster images; image-heavy lesson
authoring is scheduled for Q3 2026 once the first pilot has surfaced which
visuals students actually find most useful.

## Conventions

- Filenames: `lesson-NN-slug-N.png` (e.g. `lesson-01-marine-plastic-1.png`).
- Resolution: 1200 × 800 PNG. RGB. Under 300 KB each.
- License: CC-BY-4.0 with attribution to "TideGuard AI". External images
  must keep their original license; declare it in this file when adding.
- Source files (Inkscape SVG, Figma export) live under `content/lessons/img/_sources/`.

## Adding an illustration

1. Drop the PNG into this directory using the convention above.
2. Reference it from the lesson markdown:
   ```markdown
   ![Plastic gyres in the world ocean](img/lesson-01-marine-plastic-1.png)
   ```
3. Add a row to the table below.

## Inventory (placeholder)

| File | Lesson | Topic | License |
|------|--------|-------|---------|
| — | 01 | World plastic gyres (incl. Black Sea outline) | CC-BY-4.0 |
| — | 02 | Plastic lifecycle diagram | CC-BY-4.0 |
| — | 04 | Annotated screenshot of the TideGuard map | CC-BY-4.0 |
