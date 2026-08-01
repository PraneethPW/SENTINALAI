import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Trash2, Users } from 'lucide-react'
import { useState } from 'react'
import { api } from '../lib/api'

type Contact = { id:number; name:string; phone:string; relationship:string }
const blank = { name:'', phone:'', relationship:'' }

export function Contacts() {
  const client = useQueryClient()
  const [form, setForm] = useState(blank)
  const [editing, setEditing] = useState<number | null>(null)
  const contacts = useQuery({ queryKey:['contacts'], queryFn:async () => (await api.get<Contact[]>('/contacts')).data })
  const save = useMutation({
    mutationFn: () => editing ? api.put(`/contacts/${editing}`, form) : api.post('/contacts', form),
    onSuccess: () => { client.invalidateQueries({ queryKey:['contacts'] }); setForm(blank); setEditing(null) },
  })
  const remove = useMutation({ mutationFn:(id:number) => api.delete(`/contacts/${id}`), onSuccess:() => client.invalidateQueries({ queryKey:['contacts'] }) })
  return <div className="mx-auto max-w-4xl"><p className="text-sm font-semibold text-cyan">YOUR SAFETY CIRCLE</p><h1 className="mt-1 text-3xl font-semibold">Trusted contacts</h1><p className="mt-2 text-slate-400">The people you choose for recovery and urgent security updates.</p><section className="glass mt-7 rounded-lg p-5"><h2 className="font-semibold">{editing ? 'Edit contact' : 'Add someone you trust'}</h2><div className="mt-4 grid gap-3 md:grid-cols-3"><input placeholder="Full name" value={form.name} onChange={e => setForm({...form,name:e.target.value})}/><input placeholder="Phone number" value={form.phone} onChange={e => setForm({...form,phone:e.target.value})}/><input placeholder="Relationship" value={form.relationship} onChange={e => setForm({...form,relationship:e.target.value})}/></div><div className="mt-3 flex gap-2"><button disabled={!form.name || !form.phone || !form.relationship || save.isPending} onClick={() => save.mutate()} className="flex items-center gap-2 rounded-md bg-cyan px-4 py-2 text-sm font-semibold text-ink"><Plus size={16}/>{editing ? 'Save changes' : 'Add contact'}</button>{editing && <button onClick={() => {setEditing(null);setForm(blank)}} className="rounded-md border border-white/15 px-4 text-sm">Cancel</button>}</div></section><section className="mt-5 grid gap-3 md:grid-cols-2">{contacts.data?.map(contact => <article key={contact.id} className="glass flex items-center gap-4 rounded-lg p-5"><span className="grid h-10 w-10 place-items-center rounded-full bg-lime text-ink"><Users size={18}/></span><div className="min-w-0 flex-1"><p className="font-semibold">{contact.name}</p><p className="text-sm text-slate-400">{contact.relationship} · {contact.phone}</p></div><button aria-label={`Edit ${contact.name}`} onClick={() => {setEditing(contact.id);setForm({name:contact.name,phone:contact.phone,relationship:contact.relationship})}} className="p-2 text-cyan"><Pencil size={17}/></button><button aria-label={`Delete ${contact.name}`} onClick={() => remove.mutate(contact.id)} className="p-2 text-coral"><Trash2 size={17}/></button></article>)}</section></div>
}
