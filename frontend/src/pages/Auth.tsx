import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { AlertCircle, ArrowRight } from 'lucide-react'
import { useForm } from 'react-hook-form'
import type React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { api } from '../lib/api'
import { Logo } from '../components/Logo'

const schema = z.object({ email:z.string().email('Enter a valid email'), password:z.string().min(8,'Use at least 8 characters'), full_name:z.string().min(2,'Tell us your name').optional() })
type Values = z.infer<typeof schema>
export function Auth({ registerMode=false }:{ registerMode?:boolean }) {
  const navigate=useNavigate(); const form=useForm<Values>({ resolver:zodResolver(schema), defaultValues:{email:'',password:'',full_name:''} })
  const mutation=useMutation({ mutationFn:(v:Values)=>api.post(registerMode?'/auth/register':'/auth/login',v), onSuccess:({data})=>{localStorage.setItem('sentinel_token',data.access_token);navigate('/app')} })
  return <main className="grid min-h-screen place-items-center grid-bg p-5"><div className="glass w-full max-w-md rounded-lg p-7 shadow-glow"><Link to="/"><Logo/></Link><h1 className="mt-10 text-3xl font-semibold">{registerMode?'Set up your guardian':'Welcome back'}</h1><p className="mt-2 text-slate-400">{registerMode?'Your protected workspace is a few details away.':'Sign in to see what SentinelAI is watching for.'}</p><form onSubmit={form.handleSubmit((v)=>mutation.mutate(v))} className="mt-7 space-y-4">{registerMode&&<Field label="Name" error={form.formState.errors.full_name?.message}><input {...form.register('full_name')} /></Field>}<Field label="Email" error={form.formState.errors.email?.message}><input type="email" {...form.register('email')} /></Field><Field label="Password" error={form.formState.errors.password?.message}><input type="password" {...form.register('password')} /></Field>{mutation.error&&<p className="flex gap-2 text-sm text-coral"><AlertCircle size={17}/>Unable to continue. Check your details.</p>}<button disabled={mutation.isPending} className="flex w-full items-center justify-center gap-2 rounded-md bg-cyan py-3 font-semibold text-ink disabled:opacity-60">{mutation.isPending?'Securing session...':registerMode?'Create account':'Sign in'}<ArrowRight size={17}/></button></form><p className="mt-6 text-center text-sm text-slate-400">{registerMode?'Already protected?':'New to SentinelAI?'} <Link className="text-cyan" to={registerMode?'/login':'/register'}>{registerMode?'Sign in':'Create an account'}</Link></p></div></main>
}
function Field({label,error,children}:{label:string;error?:string;children:React.ReactNode}) { return <label className="block text-sm font-medium">{label}<span className="mt-2 block">{children}</span>{error&&<span className="mt-1 block text-xs text-coral">{error}</span>}</label> }
