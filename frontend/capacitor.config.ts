import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.praneethpw.sentinelai',
  appName: 'SentinelAI',
  webDir: 'dist',
  server: { androidScheme: 'https', cleartext: true },
}

export default config
