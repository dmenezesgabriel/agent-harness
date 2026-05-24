# Project Context

This file defines the domain vocabulary for this project. Skills read it at session start to use consistent terminology in task names, requirements, acceptance criteria, test names, and code.

Update this file when a domain term is first defined or clarified. Do not batch updates — add terms as they emerge.

---

## Domain terms

<!--
Each entry follows this format:

### <Term>

**Definition**: One sentence. What it means in this project specifically.
**Usage**: How it appears in code, APIs, tasks, or the UI (e.g., model name, route prefix, event name).
**Constraints**: Key rules that apply to this term (optional).

-->

### Example: Project

**Definition**: A named workspace owned by one user that groups members, tasks, and settings.
**Usage**: `Project` model, `POST /projects` route, "project" in all task and requirement text.
**Constraints**: A project must have an owner; it cannot exist without one.

### Example: Member

**Definition**: A user who belongs to a project with a role (owner, admin, or member).
**Usage**: `ProjectMember` join model, "member" in invitation and permission task text.
**Constraints**: Roles are: owner (one per project), admin, member. Permissions differ per role.

---

## Decisions and constraints

<!--
Record cross-cutting decisions that are not captured in an ADR but affect naming, behavior, or conventions.
-->

### Example: API error format

All API errors use `{ code: string, message: string, field?: string }`. Use this shape in all task requirements and acceptance criteria involving validation or error handling.

---

## Out of scope

<!--
Record what this project explicitly does not do, to avoid re-litigating decisions in planning sessions.
-->

<!-- Example: This project does not support multi-tenancy. All data is scoped to a single organization. -->
