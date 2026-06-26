# Mongolia Capital Markets — Component Conventions

## Wrapping and setup

No global provider or theme wrapper is required. All components are self-contained and import their styles via Tailwind CSS classes baked into the bundle. Render any component directly with `ReactDOM.createRoot(el).render(<Component .../>)`.

## Styling idiom

This project uses **Tailwind CSS v3 utility classes** as its only styling mechanism. There are no `styled-components`, no CSS Modules, and no prop-based theming. Layouts use `flex`, `grid`, and spacing utilities. Color palette is Tailwind's default slate/gray/blue/green/red scale.

Key class families in use:
- Layout: `flex flex-wrap gap-3`, `grid grid-cols-2 sm:grid-cols-3`, `max-w-7xl mx-auto px-6`
- Cards/containers: `bg-white rounded-xl shadow-sm border border-gray-100`
- Typography: `text-sm font-medium text-gray-800`, `text-xs text-gray-400 uppercase tracking-wide`
- Data values: `font-mono`, `text-blue-700 font-semibold`, `text-green-500` (gains), `text-red-500` (losses)
- Interactive: `hover:bg-blue-50 transition-colors cursor-pointer`

To add new layout glue around a component, use Tailwind classes directly on the wrapper element. Do NOT import an external stylesheet — the bundle's `_ds_bundle.css` carries all required CSS and is already loaded via `styles.css`.

## Where the truth lives

- **Component styles**: `_ds_bundle.css` (imported by `styles.css`)
- **Per-component API**: `components/<group>/<Name>/<Name>.d.ts` and `<Name>.prompt.md`

## Data interfaces

All `NUMERIC` database columns arrive as `string | null` in component props (Pydantic serializes Decimal to string to avoid float precision loss on large MNT values). Pass numeric data as strings: `value="250000000"` not `value={250000000}`.

## Idiomatic build snippet

```tsx
import { QuotesTable, SummaryStrip } from 'frontend';

const QUOTES = [
  { id: 1, ticker: 'APU', last: '9200', change: '150', change_pct: '1.66',
    value: '250200000', open: '9050', high: '9250', low: '9000',
    trade_time: '2026-06-25T09:00:00', volume: 27174,
    prev_close: '9050', close: null, bid_price: null, bid_qty: null,
    ask_price: null, ask_qty: null },
];

export function Dashboard() {
  return (
    <div className="bg-gray-50 p-6">
      <SummaryStrip quotes={QUOTES} />
      <QuotesTable quotes={QUOTES} onSelectTicker={(t) => console.log(t)} />
    </div>
  );
}
```
