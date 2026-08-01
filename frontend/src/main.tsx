import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './index.css'
import { AppShell } from './components/AppShell'
import { Assistant } from './pages/Assistant'
import { Auth } from './pages/Auth'
import { Contacts } from './pages/Contacts'
import { Dashboard } from './pages/Dashboard'
import { Landing } from './pages/Landing'
import { LiveProtection } from './pages/LiveProtection'
import { Settings } from './pages/Settings'
import { SafetyCenter } from './pages/SafetyCenter'
import { Threats } from './pages/Threats'

const client = new QueryClient()
function Protected() { return localStorage.getItem('sentinel_token') ? <AppShell/> : <Navigate to="/login" replace/> }
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={client}><BrowserRouter><Routes><Route path="/" element={<Landing/>}/><Route path="/login" element={<Auth/>}/><Route path="/register" element={<Auth registerMode/>}/><Route path="/app" element={<Protected/>}><Route index element={<Dashboard/>}/><Route path="live" element={<LiveProtection/>}/><Route path="safety" element={<SafetyCenter/>}/><Route path="threats" element={<Threats/>}/><Route path="contacts" element={<Contacts/>}/><Route path="assistant" element={<Assistant/>}/><Route path="settings" element={<Settings/>}/></Route><Route path="*" element={<Navigate to="/" replace/>}/></Routes></BrowserRouter></QueryClientProvider></React.StrictMode>)
