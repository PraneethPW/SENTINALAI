import { useEffect, useRef, useState } from 'react'

const socketUrl = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8001/api/v1/ws'
export function useRealtime(onMessage: (payload: {type:string;title?:string;description?:string}) => void) {
  const [connected,setConnected] = useState(false)
  const callback = useRef(onMessage)
  useEffect(() => { callback.current = onMessage }, [onMessage])
  useEffect(() => {
    const token = localStorage.getItem('sentinel_token')
    const socket = new WebSocket(`${socketUrl}?token=${encodeURIComponent(token ?? '')}`)
    socket.onopen = () => setConnected(true)
    socket.onclose = () => setConnected(false)
    socket.onmessage = event => callback.current(JSON.parse(event.data))
    return () => socket.close()
  }, [])
  return connected
}
