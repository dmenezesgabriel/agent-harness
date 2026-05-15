# Component-Driven Design Reference

## Purpose

Use this reference when the implementation route is frontend/UI-heavy and the work benefits from a design-system mindset.

Goal: build and evolve reusable UI systems, not just individual pages.

## Design systems, not pages

Treat screens as compositions of reusable interface parts. Prefer shared patterns, states, and rules over one-off page-specific implementations.

This improves consistency, reuse, testing, and maintenance across the product.

## Atomic Design levels

Use Brad Frost's Atomic Design as a **mental model**, not a strict build order. Work across levels as needed; do not force a bottom-up-only sequence.

### Atoms
Smallest useful UI building blocks: buttons, inputs, labels, icons, colors, type styles.

**Example:** a primary button component with accessible disabled and loading states.

### Molecules
Small groups of atoms working together for one focused job.

**Example:** a search field made from an input, label, and submit button.

### Organisms
Composed sections made from molecules and atoms that form a distinct part of the interface.

**Example:** a site header with logo, navigation, search, and account actions.

### Templates
Page-level layouts that place organisms into structure without committing to final content.

**Example:** a product listing template with header, filters, results area, and footer.

### Pages
Concrete instances of templates with real content and realistic states.

**Example:** a search results page showing empty, loading, error, and populated results.

## Practical workflow

### Component isolation
Build and review components in isolation when possible. Use realistic props, fixtures, and content, not only idealized happy-path examples. Define key states early: default, hover/focus, disabled, loading, empty, error, and responsive variations where relevant.

### Composition
Keep components small enough to combine predictably. Push shared behavior into reusable parts; keep page-specific wiring at higher levels.

### Interface inventory / UI audit
Before building new UI, inspect the existing product. Identify repeated patterns, near-duplicates, inconsistent variants, and missing shared primitives.

### Pattern libraries / documentation
Document components, states, inputs, constraints, and intended usage in a pattern library or equivalent reference. Show both isolated examples and composed usage.

### Maintenance / governance
Treat the design system as a living product. Assign ownership, review new variants carefully, remove duplicates, and update documentation when behavior or styling changes.

## Short practical guidance

- Prefer extending an existing component before adding a one-off page variant.
- Name components by role and intent, not by one screen where they first appeared.
- Treat accessibility as part of the component contract: semantics, labels, keyboard behavior, and focus handling belong in the design and tests.
- Test visible behavior and accessibility in isolation, then verify composition in real page flows.
- Use pages to validate real content and edge cases, not to define the system from scratch.

## References

- Brad Frost, *Atomic Design*, Chapter 1: "Atomic Design". https://atomicdesign.bradfrost.com/chapter-1/
- Brad Frost, *Atomic Design*, Chapter 2: "Atomic Design Methodology". https://atomicdesign.bradfrost.com/chapter-2/
- Brad Frost, *Atomic Design*, Chapter 3: "Pattern Libraries". https://atomicdesign.bradfrost.com/chapter-3/
- Brad Frost, *Atomic Design*, Chapter 4: "Designing Systems". https://atomicdesign.bradfrost.com/chapter-4/
- Brad Frost, *Atomic Design*, Chapter 5: "Creating a Living Design System". https://atomicdesign.bradfrost.com/chapter-5/
