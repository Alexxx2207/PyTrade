import { createRoot } from 'react-dom/client'
import './index.css'
import './config'
import { App } from './components/app.tsx'


createRoot(document.getElementById('root')!).render(
    <App />
)
