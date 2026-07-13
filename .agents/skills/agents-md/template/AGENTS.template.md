# <Project Name>

<One-sentence pitch: what it is + the loop it runs.>

Two audiences: **<operators>** (<who>) and **<clients>** (<who>).  <!-- delete if single audience -->

---

## Documentation Map

Detailed specs live in `docs/`. This file is the entry point.

| Domain       | File                   | What it covers                                  |
| ------------ | ---------------------- | ----------------------------------------------- |
| <Domain>     | `docs/<FILE>.md`       | <one line>                                      |

> **Read order:** A → B → C

---

## Agent Rules

### Communication

- Be extremely concise; grammar can be sacrificed.
- Do not guess; verify from repo files first.
- Label uncertain content `[Unverified]` or `[Speculation]`.
- Include `[Probability: x%]` for non-trivial uncertain claims.
- Trust official docs first (framework/vendor docs, primary sources).

### Plan Mode

- Short ordered bullets; avoid long prose.
- End every plan with `Ask: ...` or `Ask: none`.

---

## Runtime Baseline

| Layer        | Stack                                  |
| ------------ | -------------------------------------- |
| Framework    | <e.g. TanStack Start / Next.js / Remix / Vite + React> |
| UI           | React <x>.x · Tailwind CSS <x>.x       |
| Language     | TypeScript <x>.x (strict)              |
| Database     | <Postgres / Mongo / SQLite> · <Prisma / Drizzle> |
| Auth         | <Better Auth / NextAuth / Clerk / ...> |
| State        | <Redux Toolkit / Zustand / Context / none> |
| AI           | <provider SDKs, if any>                |
| Payments     | <Stripe / none>                        |
| Storage      | <S3 + CloudFront / R2 / GCS / none>    |
| Email        | <SES / Resend / Postmark / none>       |
| Cache        | <Redis / Upstash / none>               |
| Hosting      | <Vercel / Fly / Railway / Render / Cloudflare> |
| Observability| <Sentry / OpenTelemetry / Axiom / none>|
| Testing      | <Vitest / Jest> · Testing Library · <Playwright / none> |
| Package mgr  | <pnpm / npm / bun / yarn>              |

---

## <Core Domain Abstraction>  <!-- OPTIONAL, delete if N/A -->

<One screen describing the project's central abstraction, if any. Examples
 of domains where this section earns its keep:

 - Order/booking lifecycle with multi-step state machine
 - Multi-tenant org/membership/role inheritance
 - Content model with i18n resolution rules
 - Workflow engine with template → instance → refinement chain
 - Subscription/billing/plan tiers with per-feature gating

 Include lifecycle diagrams in fenced code blocks, config inheritance rules,
 and any per-instance override surface. If the project does not have such an
 abstraction, delete this section entirely.>

---

## Project Layout

```
src/
├── routes/                # or app/, pages/
│   └── ...
├── components/{atoms,molecules,organisms}/
├── lib/
└── ...
prisma/
└── schema.prisma          # or drizzle/schema.ts
docs/
└── ...
```

---

## API Surface

<One sentence on the dominant pattern: server functions, server actions, REST handlers.>

Standalone API routes (only for protocol-bound endpoints):

```
api/auth/$.ts         , <auth catch-all>
api/<webhooks>/...    , <description>
```

Key server functions / actions: `<fn1>`, `<fn2>`, ...

---

## Key Data Models

See `prisma/schema.prisma` (or equivalent) for the full schema. Core entities:

**<Category>:** Model, Model
**<Category>:** Model, Model

---

## Commands

```bash
pnpm dev          # <short note>
pnpm build        # <short note>
pnpm lint         # ESLint / Biome
pnpm typecheck    # tsc --noEmit
pnpm test         # Vitest
pnpm db:generate  # Prisma client (or drizzle-kit generate)
pnpm db:push      # Push schema (Mongo) / migrate (SQL)
```

<Call out any common command that is **missing** (e.g. "no `typecheck` script, run `pnpm exec tsc --noEmit`").>

---

## Coding Rules

**Do:** Use path aliases (`@/*` or `~/*` or `#/*`), type imports (`import type ...` / `import { type ... }`), **`const` object + literal-union types for variants** (not TS `enum`, rejected by TS 5.5+ `--erasableSyntaxOnly` and Node's native TS loader), `classNames()` for conditional classes, atomic architecture (`atoms → molecules → organisms`), PascalCase component files, barrel exports per directory, type-guard predicate functions (`value is Type`) instead of `as` assertions. Once a `className` has **more than 3 utility classes**, switch to `classNames()` with one class per argument.

**Don't:** Inline imports, single-letter variables, nested ternaries, comments inferable from code, `&&` in JSX (use ternary + `null`), inline complex expressions in JSX props (extract to a named `const` first), type assertions (`as`), `eslint-disable-next-line` comments, fix the root cause instead. Never hand-edit generated files (`routeTree.gen.ts`, `src/generated/prisma/**`, lockfiles). TS `enum` in app-authored code (Prisma-generated enums in `schema.prisma` are fine to consume).

<Add 1-3 project-specific subsections only for non-obvious patterns:
 e.g. **AI generation:** ..., **Sentry instrumentation:** ..., **i18n:** ..., **Payments:** ..., **Image uploads:** ...>

---

## Safety

### Allowed without prompt

Read/search files, single-file lint/typecheck/format, targeted tests, `prisma generate`, git commit (with hooks).

### Ask first

Install/remove deps, delete files, full builds, `prisma db push` / `migrate` against any non-local DB, external service ops, force-push.

### Never

`git push` without explicit request. Destructive git commands (`reset --hard`, `clean -fd`, `branch -D`, force-push to `main`). List files outside the project. Read `.env` or any `.env.*` file except `.env.example`, they contain live secrets. Reason from `.env.example` / error output instead. Bypass hooks (`--no-verify`) or signing (`--no-gpg-sign`) unless explicitly asked. Hand-edit generated files.

---

## Quality Gates

Before PR: `pnpm lint` → `pnpm typecheck` (or `pnpm exec tsc --noEmit`) → `pnpm test` → `pnpm build`.

PR titles: `^(feat|fix|refactor|docs|test|chore)(\(|:).*`

---

## Risk Areas (Plan First)

<Comma-separated: auth/session flows, payment/webhook handlers, state machines, schema changes, AI generation pipeline, role/permission checks, env-variable usage, generated-file boundaries.>
