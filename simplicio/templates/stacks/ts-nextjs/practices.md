# ts-nextjs best practices (planner reference)

## Project structure
- `src/app/<route>/page.tsx` — server components by default; add `"use client"` only when state/effect needed
- `src/app/<route>/route.ts` — route handlers for API endpoints (GET/POST/etc. exported functions)
- `src/lib/` — pure modules (db client, schema, formatters); never import from app/
- `src/components/` — reusable UI; one component per file; co-located test in `<Name>.test.tsx`

## Typing
- TS strict mode on (`tsconfig.json`: `"strict": true`)
- Server actions typed with explicit input + output schemas (zod recommended but optional)
- No `any` — use `unknown` + type-narrowing if truly dynamic
- Props typed inline or via named interface; never `props: any`

## React patterns
- Server components for data-fetching pages; client components for interactivity
- Suspense boundaries around streamed sections
- No `useEffect` for data fetching — use server components or react-query
- Forms: server actions with progressive enhancement (`<form action={action}>`)

## Tests
- `vitest` for unit + integration; `@testing-library/react` for component tests
- One `.test.tsx` per source file; named after the source module
- Playwright spec per user-facing flow under `playwright/`

## API design
- Route handlers in `src/app/api/<resource>/route.ts`
- Return `Response.json(...)` or `NextResponse.json(...)`; never raw strings
- Status codes explicit (`{ status: 201 }`)
- Errors via `NextResponse.json({ error: ... }, { status: 4xx })`

## Tasks planner SHOULD produce
- Order: tsconfig + ESLint setup → db client → schema → route handlers → components → e2e
- Each task touches ONE file
- `verify` per task references the test file directly (e.g. `pnpm vitest run src/lib/db.test.ts`)
- `test_command` = `pnpm vitest run`; `lint_command` = `pnpm eslint .`
