import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
{% if website.use_tailwind %}
import './styles/globals.css'
{% endif %}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
