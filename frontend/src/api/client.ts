const base=import.meta.env.VITE_API_BASE_URL ?? '/api';
export async function api<T>(path:string, init?:RequestInit):Promise<T>{const r=await fetch(`${base}${path}`,init);if(!r.ok)throw new Error(`Request failed (${r.status})`);return r.json() as Promise<T>}
