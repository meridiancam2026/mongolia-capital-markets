# Design Sync — Notes

## Repo shape

- Private Vite React application (`frontend/`), NOT a published npm package.
- No Storybook. Shape = `package`.
- No built `dist/` — converter runs with `--entry ./frontend/src/components/index.ts` (the barrel file at `frontend/src/components/index.ts`).
- Node.js lives in **WSL2 Ubuntu** — all converter commands must run via `wsl.exe -d Ubuntu -- /bin/bash -ic "..."` from PowerShell, or directly in a WSL2 terminal.
- `pkg: "frontend"` is a generic name; without `--entry`, the converter tries `node_modules/frontend/` and crashes. Always pass `--entry`.

## Playwright / render check

Chromium headless does not launch in this WSL2 environment (sandbox failure: "Target page, context or browser has been closed"). All syncs must use `--no-render-check`. The user accepted unverified bundle on 2026-06-25.

System deps installed: `npx playwright install-deps chromium` was run. Still fails. May require kernel-level sandbox config.

## Build command

```bash
cd /mnt/c/Users/CameronThomas/OneDrive\ -\ Meridian\ Universal/Documents/02_Agent\ Projects/Local\ Capital\ Markets/mongolia-capital-markets
node .ds-sync/package-build.mjs \
  --config .design-sync/config.json \
  --node-modules frontend/node_modules \
  --entry ./frontend/src/components/index.ts \
  --out ./ds-bundle
node .ds-sync/package-validate.mjs ./ds-bundle --no-render-check
```

## Components

- **PriceHistoryChart**: Floor card intentionally — it calls `useTickerHistory()` which makes a live API call. Cannot render in a static preview without mocking the hook. Author a preview only if the hook is extracted as a prop (`history: Quote[]`).
- **Modal**: `cardMode: "single", viewport: "900x600"` — fixed overlay escapes card bounds in grid mode. Currently a floor card (no authored preview). Future author: wrap in a `<div style={{position:"relative",height:"600px",overflow:"hidden"}}>`.
- **FxCard**: `indicator` prop requires both `value` (as string) and `reference_date` (not optional). Previewed with 4 currency pairs.
- All NUMERIC fields are `string | null` — pass monetary values as strings not numbers.

## Known render warns

(empty — render check not run)

## Re-sync risks

- **Tailwind CSS classes**: The `_ds_bundle.css` is ~0 KB because Tailwind's CSS isn't extracted at build time — the styles live in the Vite app's built CSS, not a standalone stylesheet. This means components appear unstyled in a fresh design unless the full Tailwind stylesheet is imported. If visual fidelity issues appear, set `cssEntry` to the built `frontend/dist/assets/*.css` after running `vite build`.
- **componentSrcMap paths**: Each entry is relative to `frontend/`. If any component file is moved or renamed, the map must be updated or that component drops from the sync.
- **No `.d.ts` tree**: Props bodies in `.d.ts` files are `[key: string]: unknown` because there are no pre-built type declarations. Richer types require a `tsc --declaration --emitDeclarationOnly` step.
- **Barrel file**: `frontend/src/components/index.ts` is the synth entry — it must stay in sync with the actual component files.
