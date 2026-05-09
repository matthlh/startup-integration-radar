# Agent instructions

All AI coding agents should follow `CLAUDE.md`.

## Agent roles

### Product agent

Owns PRD, workflows, scoring philosophy, and user experience.

### Backend agent

Owns deterministic pipeline, API, CLI, tests, providers, exports.

### Frontend agent

Owns dashboard, review cards, evidence visibility, and Figma Make implementation.

### GTM agent

Owns ICP logic, outreach templates, Clay columns, persona targeting, and demo concepts.

## Safe operating mode

Default to local/dry-run behavior. Do not use Exa, Claude, Clay, email, or paid APIs unless explicitly configured and requested.
