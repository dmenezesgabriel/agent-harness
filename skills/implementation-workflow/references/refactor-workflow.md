# Refactor Workflow

## Characterize current behavior first

Before changing structure, protect current observable behavior.

Use characterization tests or other stable checks when the existing behavior is important but not well documented.

## Behavior-preserving change

Refactor in small steps that keep behavior stable:

1. add or confirm protection
2. make one structural improvement
3. run targeted checks
4. repeat

Do not mix new behavior into the same step unless the behavior change is already separately protected.

## Improve boundaries incrementally

Use refactoring to improve:

- ownership
- cohesion
- dependency direction
- naming
- side-effect boundaries
- duplicated policy

Make one boundary improvement at a time instead of rewriting the whole module.

## Avoid redesign without protection

Do not combine big redesign with unprotected code movement.

If the current design is poor, still establish behavior protection first. Safer small refactors beat a large cleanup that changes many responsibilities at once.
