import axios from 'axios'
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8001/api/v1' })
api.interceptors.request.use((config) => { const token = localStorage.getItem('sentinel_token'); if (token) config.headers.Authorization = `Bearer ${token}`; return config })
export type Dashboard = { score:number; score_label:string; devices:{id:number;name:string;platform:string;status:string;risk_score:number;last_seen:string}[]; events:{id:number;title:string;severity:string;description:string;occurred_at:string}[]; recommendations:string[] }
