export type Health = {status:'ok';service:'playground-api';api_version:'v1'};
export async function getHealth(signal: AbortSignal): Promise<Health> {
  const response = await fetch('/api/v1/health', {signal, cache:'no-store'});
  if (!response.ok) throw new Error('API unavailable');
  const data: unknown = await response.json();
  if (!data || typeof data !== 'object' || !('status' in data) || data.status !== 'ok' || !('service' in data) || data.service !== 'playground-api' || !('api_version' in data) || data.api_version !== 'v1') throw new Error('Unexpected API response');
  return {status:'ok',service:'playground-api',api_version:'v1'};
}
