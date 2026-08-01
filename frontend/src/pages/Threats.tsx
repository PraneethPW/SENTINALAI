import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, CircleAlert, ShieldAlert } from 'lucide-react'
import { api } from '../lib/api'
import { BellRing, Radio } from 'lucide-react'
import { useCallback, useState } from 'react'
import { useRealtime } from '../hooks/useRealtime'

type Alert = { id:number; title:string; description:string; severity:string; occurred_at:string; acknowledged:boolean }

export function Threats() {
  const client = useQueryClient()
  const alerts = useQuery({ queryKey:['alerts'], queryFn:async () => (await api.get<Alert[]>('/alerts')).data })
  const acknowledge = useMutation({
    mutationFn: (id:number) => api.post(`/alerts/${id}/acknowledge`),
    onSuccess: () => client.invalidateQueries({ queryKey:['alerts'] }),
  })
  const [permission,setPermission] = useState(Notification.permission)
  const testAlert = useMutation({ mutationFn:() => api.post('/alerts/test') })
  const handleMessage = useCallback((payload:{type:string;title?:string;description?:string}) => { if(payload.type === 'security_alert') { client.invalidateQueries({queryKey:['alerts']}); if(Notification.permission === 'granted') new Notification(payload.title ?? 'SentinelAI alert',{body:payload.description}) } }, [client])
  const connected = useRealtime(handleMessage)
  const enableNotifications = async () => setPermission(await Notification.requestPermission())
  return <div className="mx-auto max-w-4xl"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-semibold text-cyan">SECURITY INBOX</p><h1 className="mt-1 text-3xl font-semibold">Threat detection</h1><p className="mt-2 text-slate-400">Live signals from your Sentinel workspace, delivered as they happen.</p></div><div className="flex gap-2"><button onClick={() => testAlert.mutate()} className="rounded-md bg-cyan px-3 py-2 text-sm font-semibold text-ink">Run live security check</button>{permission !== 'granted' && <button onClick={enableNotifications} className="rounded-md border border-white/20 p-2 text-cyan" aria-label="Enable browser notifications"><BellRing size={18}/></button>}</div></div><div className="mt-5 flex items-center gap-2 text-xs text-slate-400"><Radio size={14} className={connected ? 'text-lime' : 'text-coral'}/>{connected ? 'Live connection active' : 'Reconnecting to live security feed...'}</div><div className="mt-5 space-y-3">{alerts.data?.map((alert) => <article key={alert.id} className={`glass flex flex-wrap items-start gap-4 rounded-lg p-5 ${alert.acknowledged ? 'opacity-60' : ''}`}><span className={`mt-1 rounded-full p-2 ${alert.severity === 'medium' ? 'bg-coral/15 text-coral' : 'bg-lime/15 text-lime'}`}>{alert.severity === 'medium' ? <CircleAlert size={19}/> : <ShieldAlert size={19}/>}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h2 className="font-semibold">{alert.title}</h2><span className="rounded-full bg-white/10 px-2 py-0.5 text-xs uppercase text-slate-300">{alert.severity}</span></div><p className="mt-1 text-sm leading-6 text-slate-400">{alert.description}</p><p className="mt-2 text-xs text-slate-500">{new Date(alert.occurred_at).toLocaleString()}</p></div>{alert.acknowledged ? <span className="flex items-center gap-1 text-sm text-lime"><CheckCircle2 size={16}/> Reviewed</span> : <button onClick={() => acknowledge.mutate(alert.id)} className="rounded-md border border-cyan/50 px-3 py-2 text-sm text-cyan">Mark reviewed</button>}</article>)}</div></div>
}
