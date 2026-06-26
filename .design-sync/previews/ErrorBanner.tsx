import { ErrorBanner } from 'frontend';

export function NetworkError() {
  return <ErrorBanner message="Failed to connect to the market data API. Please try again." />;
}

export function DataError() {
  return <ErrorBanner message="No quote data returned for this security." />;
}
