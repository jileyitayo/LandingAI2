import { useEffect } from 'react'
{% for component in page.components %}
import {{ component.name }} from '@/components/{{ component.name }}'
{% endfor %}

const {{ page.name|title }} = () => {
  useEffect(() => {
    document.title = '{{ page.title }} - {{ website.title }}'
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {% for component in page.components %}
      <{{ component.name }} 
        {% for prop, value in component.props.items() %}
        {{ prop }}={{{ value|tojson }}}
        {% endfor %}
      />
      {% endfor %}
    </div>
  )
}

export default {{ page.name|title }}