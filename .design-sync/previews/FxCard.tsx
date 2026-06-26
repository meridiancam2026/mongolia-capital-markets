import { FxCard } from 'frontend';

const makeRate = (indicator: string, value: string, date: string) => ({
  id: 1, indicator, value, reference_date: date, source: 'BOM',
});

export function USD() {
  return <FxCard indicator={makeRate('FX_USD_MNT', '3430.50', '2026-06-25')} />;
}

export function CNY() {
  return <FxCard indicator={makeRate('FX_CNY_MNT', '473.80', '2026-06-25')} />;
}

export function EUR() {
  return <FxCard indicator={makeRate('FX_EUR_MNT', '3718.20', '2026-06-25')} />;
}

export function JPY() {
  return <FxCard indicator={makeRate('FX_JPY_MNT', '22.41', '2026-06-25')} />;
}
