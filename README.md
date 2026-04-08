# Skills Framework

A modular system for defining and running reusable workflows ("skills") across projects.

> Skills encapsulate project-specific logic, validation steps, and automation tasks in a structured and scalable way. While originally designed for use with Claude Code, this framework is intentionally tool-agnostic so it can be adapted for other environments and tooling.

---

## Table of Contents

- [What is a Skill?](#what-is-a-skill)
- [Directory Structure](#directory-structure)
- [Skill Definition (SKILL.md)](#skill-definition-skillmd)
- [Workspaces](#workspaces)
- [Adding a New Skill](#adding-a-new-skill)
- [Adding a New Workspace](#adding-a-new-workspace)
- [Tool Agnostic Design](#tool-agnostic-design)
- [Best Practices](#best-practices)

---

## What is a Skill?

A **skill** is a self-contained unit of functionality that:

- Performs a specific task (e.g., validation, migration checks, reporting)
- Has its own documentation and instructions
- Can be invoked programmatically or via supported interfaces (CLI, chat tools, scripts, etc.)

Each skill lives in its own directory and is defined primarily through a `SKILL.md` file.

---

## Directory Structure

```text
skills/
├── <workspace-name>/        # Logical grouping of related skills
│   ├── <skill-name>/        # Individual skill
│   │   ├── SKILL.md         # Core definition and instructions
│   │   ├── assets/          # (Optional) Supporting files
│   │   └── scripts/         # (Optional) Automation scripts
│   └── ...
└── ...
```

---

## Skill Definition (SKILL.md)

Each skill must include a `SKILL.md` file that defines:

| Section | Description |
|---------|-------------|
| **Purpose** | What the skill does |
| **Inputs** | Required parameters or context |
| **Execution Steps** | How the task is performed |
| **Outputs** | Expected results (logs, reports, artifacts) |
| **Constraints / Rules** | Validation logic or boundaries |

This makes each skill:

- Self-documenting
- Easy to reuse
- Easy to integrate with different tools

---

## Workspaces

Workspaces are logical groupings of related skills.

### Example Structure

```text
skills/
└── style-workspace/
    ├── verify-migration/
    └── verify-migration-token-shorthand/
```

### Example: `style-workspace`

Focuses on design token and styling workflows such as:

- Migration verification
- Token validation
- Structure consistency checks
- Report generation

---

## Adding a New Skill

1. Create a new directory under the appropriate workspace:
   ```text
   skills/<workspace>/<skill-name>/
   ```

2. Add a `SKILL.md` with:
   - Clear purpose
   - Step-by-step instructions
   - Input/output definition

3. *(Optional)* Add:
   - Scripts for automation
   - Supporting assets or templates

---

## Adding a New Workspace

If your domain doesn't fit existing workspaces:

1. Create a new workspace folder:
   ```text
   skills/<new-workspace>/
   ```

2. Add a `README.md` describing:
   - Scope of the workspace
   - Types of skills it contains

3. Add skills inside it as needed

---

## Tool Agnostic Design

This framework is intentionally not tied to any specific tool.

Skills can be executed via:

| Method | Use Case |
|--------|----------|
| CLI scripts | Manual execution |
| Node.js / Python automation | Programmatic workflows |
| IDE integrations | Developer tooling |
| AI assistants (Claude, ChatGPT, etc.) | AI-powered tasks |
| CI/CD pipelines | Automated checks |

The only requirement is the ability to read and follow the instructions defined in `SKILL.md`.

---

## Best Practices

- Keep each skill focused and single-purpose
- Avoid coupling between skills unless necessary
- Prefer composition (small reusable skills) over large monolithic ones
- Document assumptions clearly
- Ensure outputs are deterministic and easy to verify

---