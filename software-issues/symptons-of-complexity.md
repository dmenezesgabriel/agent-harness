# Complexity

_One  of the most important goals of good software design is for a system to be obvious. This is the opposite of high [**cognitive load**](#cognitive-load) and [**unknown unknowns**](#unknown-unknowns). In an obvious system, a developer can quickly understand how the existing code works and what is required to make a change._

## Symptomns of Complexity

### Change amplification

A seemingly simple change requires code modifications in many different places

Specify shared constants and variables in a central place, and all individual pieces of code reference that shared value.

Good design reduce the amount of code that is affected by each design decision, so design changes do not require many code modifications.

### Cognitive load

How much a developer needs to know in order to complete a task.

### Unknown unknowns

Is not obvious which pieces of code must be modified to complete a task. There is something you need to know, but there is no way for yout to find out what it is, you won't find out about it until bugs appear after you make a change.

## Causes of complexity


Complexity is caused by two things:

- [**Dependencies**](#dependencies)
- [**Obscurity**](#obscurity)

### Dependencies

A dependency exists when a given piece of code cannot be understood and modified in isolation; the code relates in some way to other code, and the other code must be considered and/or modified if the given code is changed.

Dependencies are a fundamental part of software and cannot be completely eliminated. They are introduced intentionally as a part of software design procees, however, we must reduce dependencies and make the ones that remain simple and as obvious as possible.

### Obscurity

Occurs when important information is not obvious.

For example, some variable names without semnatic namings or numeric constants without specifying its units.

The need for extensive documentation is often a **red flag** that thedesign isn't quite right. the best way to reduce obscurity is by simplifying the system design.

## Zero tolerance philosophy

Complexity is incremental, once it has accumulated, it is hard to eliminate. In order to slow the growth of complexity we must adopt a zero tolerance philosophy.


> A philosophy of software design, 2nd edition.