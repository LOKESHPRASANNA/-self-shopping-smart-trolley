import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import axios from 'axios'
import './index.css'
import App from './App.jsx'

// Configure Axios for production (Vercel) vs Development
// locally this will be undefined/empty, so Vite proxy works.
// On Vercel, this must be set in Environment Variables.
axios.defaults.baseURL = "https://snapshop-fwdev3b8s-lokeshprasannas-projects.vercel.app";
axios.defaults.withCredentials = true; // Important for session cookies


createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
