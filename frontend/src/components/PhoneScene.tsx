import { Canvas, useFrame } from '@react-three/fiber'
import { Float } from '@react-three/drei'
import { useRef } from 'react'
import type { Mesh } from 'three'
function Phone() { const ref = useRef<Mesh>(null); useFrame((state) => { if(ref.current) ref.current.rotation.y = state.clock.elapsedTime * .24 }); return <Float speed={2} rotationIntensity={.25} floatIntensity={1.2}><mesh ref={ref}><boxGeometry args={[1.55,3.1,.18]}/><meshStandardMaterial color="#301006" metalness={.6} roughness={.23}/></mesh><mesh position={[0,0,.101]}><planeGeometry args={[1.35,2.75]}/><meshStandardMaterial color="#ff6b00" emissive="#9a2c00" emissiveIntensity={1.2}/></mesh></Float> }
export function PhoneScene() { return <div className="h-[360px] w-full"><Canvas camera={{position:[0,0,5],fov:42}}><ambientLight intensity={1.5}/><pointLight position={[2,3,4]} intensity={22} color="#ffc400"/><Phone/></Canvas></div> }
