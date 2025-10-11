import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from "@/components/ui/toaster"
import { Toaster as Sonner } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
{% for page in website.pages %}
import {{ page.name|title }} from "./pages/{{ page.name }}"
{% endfor %}

const queryClient = new QueryClient()

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          {% for page in website.pages %}
          <Route path="{{ page.path }}" element={<{{ page.name|title }} />} />
          {% endfor %}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
)

export default App