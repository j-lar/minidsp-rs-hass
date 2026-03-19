# Lovelace Dashboard Redesign (Coordination Spec)

> This is a **coordination spec**, not an implementation task in this repository.
> It captures design intent and reasoning for a follow-up implementation in an external Home Assistant dashboard repo.

## Purpose

This document captures the output of a ProtoForge ideation session so an agent (or human) can implement the dashboard redesign with the right context — especially the **why** behind the layout decisions.

- **External project**: personal, YAML-based Home Assistant Lovelace dashboard
- **Handoff target**: agent session operating in the dashboard repo fork

## Context and Problem

The current dashboard evolved incrementally and now exposes nearly every entity and control at once. That causes cognitive load and does not prioritize controls by usage frequency:

- **Frequent**: level adjustments (e.g., volume)
- **Occasional**: mode/preset switching
- **Rare**: EQ/speaker configuration and deeper controls

The existing flat entity-slug substitution pattern is still the right composability level for a shared personal template and should be preserved.

## Design Intent

Reorganize by **cognitive salience** rather than by entity type.

1. **Mode selector** (always visible, top of card)
   - Operational presets (e.g., listening, karaoke)
   - Highest-level user decision, so it appears first
2. **Active levels** (always visible, directly below mode)
   - Most frequently adjusted controls (volume, balance, similar)
   - Tuned within a mode, so they belong at the same visual layer
3. **Everything else** (collapsed by default)
   - Grouped into labeled expandable sections
   - Used intentionally and less often, so hidden until needed

Section labels and included entities are device-specific. The reusable contribution is the structure.

## Composability Constraint

This dashboard is a reference artifact and should be composable in **structure**, not falsely generic in content.

### Composable

- Layout pattern: mode switch → visible levels → collapsed sections
- Use of expander/fold containers for section structure
- Single entity-slug substitution for the primary device

### Intentionally Not Abstracted

- Preset names (hardcoded for the specific device)
- Entity IDs inside sections (clear manual substitutions)
- Section labels (with comments indicating what to rename)

Use comments to mark substitution points; avoid extra YAML templating beyond native Lovelace capabilities.

## Mode Selector Implementation Note

Preset buttons require known names at config time because Lovelace YAML is static. Using 4 hardcoded `button-card` preset actions is expected and correct. Add comments showing where to substitute names.

## Deliverable for the Implementing Agent

Produce **one Lovelace card/view YAML file** that includes:

- Mode selector button row at top
- Visible level controls below (sliders or equivalent)
- 3–5 collapsible sections using `expander-card` or `fold-entity-row`
- Inline comments at every device-specific substitution point
- Short header comment block describing layout intent and what to change

### Out of Scope

- Generalizing beyond the single-device pattern
- Dynamic templating systems
- Multiple card variants
- Re-documenting design rationale (this file already provides it)
