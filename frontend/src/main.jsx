import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import axios from 'axios'
import './index.css'
import App from './App.jsx'

// Configure Axios for production (Render / Vercel) vs Development
// Locally this will be empty, so Vite proxy (/api) works.
// On Render / Vercel, VITE_API_URL is configured.
const rawBaseURL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_PROXY_TARGET || "";
axios.defaults.baseURL = rawBaseURL ? rawBaseURL.replace(/\/+$/, '') : "";
axios.defaults.withCredentials = true; // Important for session cookies

// Resilient auth: Attach X-Username header to every request if user is logged in
axios.interceptors.request.use((config) => {
  const username = localStorage.getItem('username');
  if (username) {
    config.headers['X-Username'] = username;
  }
  return config;
});


createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
