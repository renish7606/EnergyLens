import {TriangleAlert} from 'lucide-react';
export function AnomalyBadge({label='Anomaly detected'}:{label?:string}){return <span className="inline-flex items-center gap-1.5 rounded border border-alert/50 bg-alert/10 px-2 py-1 text-xs font-medium text-alert"><TriangleAlert size={14}/>{label}</span>}
