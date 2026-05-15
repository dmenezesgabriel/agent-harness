---
name: frontend-design-audit
description: Analyze frontend UI for usability, accessibility, visual hierarchy, interaction quality, responsive behavior, and design-system consistency.
---

## Purpose

Audit frontend interfaces for concrete issues that reduce usability, accessibility, clarity, learnability, efficiency, consistency, or user trust.

Use Gestalt principles, Nielsen heuristics, WCAG, semantic HTML, interaction design, responsive design, content clarity, and design-system constraints.

This skill is framework-agnostic.

## Review Principles

### Hierarchy and Gestalt

Check whether users can quickly understand what matters, what belongs together, and what action comes next.

Flag weak hierarchy, competing focal points, poor grouping, unclear primary actions, crowded layouts, weak contrast, inconsistent alignment, poor spacing, ambiguous section boundaries, and visual noise.

Key terms: visual hierarchy, focal point, salience, information scent, proximity, similarity, continuity, common region, connectedness, figure-ground, alignment, whitespace, contrast.

### Usability Heuristics

Check whether the interface follows Nielsen’s heuristics and supports predictable task completion.

Flag missing system feedback, unclear navigation state, inconsistent patterns, poor error recovery, hidden functionality, high memory burden, missing escape paths, and unnecessary steps.

Key terms: visibility of system status, match with real world, user control and freedom, consistency and standards, error prevention, recognition over recall, flexibility, minimalist design, error recovery.

### Accessibility

Check whether the UI works with keyboard, screen readers, zoom, high contrast, and assistive technologies.

Flag missing labels, poor focus states, inaccessible custom controls, insufficient contrast, incorrect heading order, missing alt text, non-semantic markup, keyboard traps, and color-only meaning.

Key terms: WCAG, perceivable, operable, understandable, robust, semantic HTML, accessible name, focus order, focus indicator, ARIA, color contrast, keyboard navigation, screen reader support.

### Interaction and Feedback

Check whether controls clearly communicate what they do, what will happen, and what happened.

Flag unclear affordances, small hit targets, ambiguous icons, destructive actions without safeguards, disabled states without explanation, missing loading feedback, surprising behavior, and weak mapping between control and result.

Key terms: affordance, signifier, feedback, feedforward, mapping, constraint, progressive disclosure, confirmation, undo, hit target, interaction cost.

### Forms and Recovery

Check whether forms are easy to complete, validate, and recover from.

Flag unclear labels, placeholder-only labels, late validation, vague errors, inaccessible errors, hidden requirements, poor input constraints, and excessive required fields.

Key terms: field label, helper text, inline validation, error prevention, error recovery, accessible error message, validation state, input constraint.

### Navigation and Content

Check whether users understand where they are, where they can go, and what each label means.

Flag unclear navigation, inconsistent labels, deep nesting, hidden routes, weak breadcrumbs, vague buttons, unclear empty states, technical jargon, misleading copy, inconsistent terminology, and errors without recovery instructions.

Key terms: information architecture, wayfinding, breadcrumb, task flow, information scent, cognitive load, microcopy, plain language, empty state, recovery instruction, domain language.

### Responsive and Adaptive Behavior

Check whether the interface works across screen sizes, density, orientation, and input modes.

Flag broken layouts, overflow, cramped touch targets, hidden critical actions, poor reflow, desktop-only assumptions, inconsistent breakpoint behavior, and weak content priority.

Key terms: responsive design, adaptive layout, reflow, breakpoint, fluid layout, intrinsic sizing, touch target, viewport, content priority.

### Design-System Consistency

Check whether components, tokens, variants, spacing, states, and interaction patterns are used consistently.

Flag one-off styles, duplicated components, inconsistent spacing, token bypassing, unstandardized states, visual variants without semantic purpose, and component behavior that violates its contract.

Key terms: design system, component contract, design token, variant, state, spacing scale, typographic scale, pattern consistency, component reuse.

### Simplicity and Density

Do not add decoration, animation, modals, cards, steps, or layout complexity unless they improve comprehension, task completion, feedback, or accessibility.

Flag visual clutter, excessive nesting, redundant labels, decorative icons, over-fragmented UI, unnecessary modals, distracting animation, and low signal-to-noise ratio.

Key terms: minimalist design, cognitive load, signal-to-noise ratio, progressive disclosure, visual density, interaction cost, accidental complexity.

## Review Rules

Be concrete, falsifiable, and UI-specific.

Do not say:

- Improve UX
- Make it cleaner
- Improve accessibility
- Use better design
- Make it more intuitive

Instead state:

- Which user task is harder
- Which visual relationship is unclear
- Which heuristic is violated
- Which accessibility requirement is missing
- Which interaction lacks feedback
- Which copy is ambiguous
- Which component state is inconsistent
- Which layout breaks under which condition
- Which smallest change fixes the issue

Do not recommend a full redesign unless the current structure blocks task completion or accessibility.

Prefer targeted changes that preserve behavior and reduce user effort.

## Output Format

For each finding, use:

### Finding: precise frontend design issue

Priority: High | Medium | Low

Category: Hierarchy | Gestalt | Usability Heuristic | Accessibility | Interaction | Forms | Navigation | Content | Responsive | Design System | Simplicity

Issue:
Exact UI, accessibility, or interaction problem.

Evidence:
Specific screen, component, state, layout, copy, behavior, breakpoint, or flow.

Design impact:
Why it causes confusion, cognitive load, accessibility failure, weak affordance, poor recovery, slower completion, inconsistency, or broken layout.

Recommendation:
Smallest practical design or implementation change.

Target shape:
Intended layout, semantic markup, component state, interaction flow, copy, hierarchy, or accessibility behavior.

## Remediation Strategy

Prefer incremental UI fixes over broad redesigns:

1. Clarify the primary user task.
2. Fix accessibility blockers first.
3. Establish semantic HTML and accessible names.
4. Fix focus order, keyboard navigation, and focus indicators.
5. Improve hierarchy, grouping, spacing, and contrast.
6. Clarify labels, actions, errors, empty states, and recovery paths.
7. Standardize components, tokens, states, and variants.
8. Improve responsive behavior and touch targets.
9. Remove visual noise, redundant elements, and unnecessary steps.
10. Validate the flow against real tasks and edge states.

## Core Principle

Favor clear, accessible, task-oriented interfaces over decorative, inconsistent, or over-engineered UI.

Use Gestalt principles, Nielsen heuristics, WCAG, semantic HTML, and design-system constraints to reduce cognitive load, support assistive technologies, and make user actions predictable.
