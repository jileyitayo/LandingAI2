import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, Users, Award, Target } from "lucide-react"

interface AboutProps {
  title?: string
  description?: string
  story?: string
  values?: Array<{ title: string; description: string }>
  stats?: Array<{ label: string; value: string }>
  team?: Array<{ name: string; role: string; image: string }>
}

const About = ({
  title = "{{ component.content.title or 'About Us' }}",
  description = "{{ component.content.description or 'Learn more about our mission and values' }}",
  story = "{{ component.content.story or 'We are passionate about delivering exceptional results and creating meaningful experiences for our clients.' }}",
  values = [
    { title: "Quality", description: "We maintain the highest standards in everything we do." },
    { title: "Innovation", description: "We embrace new technologies and creative solutions." },
    { title: "Support", description: "We provide ongoing support and maintenance." }
  ],
  stats = [
    { label: "Happy Clients", value: "500+" },
    { label: "Projects Completed", value: "1000+" },
    { label: "Years Experience", value: "10+" }
  ],
  team = []
}: AboutProps) => {
  return (
    <section className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-foreground mb-4">{title}</h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">{description}</p>
        </div>

        {/* Story */}
        <div className="mb-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-3xl font-bold mb-6">Our Story</h3>
              <p className="text-lg text-muted-foreground leading-relaxed">{story}</p>
            </div>
            <div className="relative">
              <div className="aspect-square bg-gradient-to-br from-{{ website.color_scheme }}-500 to-{{ website.color_scheme }}-700 rounded-2xl" />
            </div>
          </div>
        </div>

        {/* Values */}
        <div className="mb-20">
          <h3 className="text-3xl font-bold text-center mb-12">Our Values</h3>
          <div className="grid md:grid-cols-3 gap-8">
            {values.map((value, index) => (
              <Card key={index} className="text-center">
                <CardHeader>
                  <div className="w-12 h-12 bg-{{ website.color_scheme }}-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="h-6 w-6 text-{{ website.color_scheme }}-600" />
                  </div>
                  <CardTitle>{value.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{value.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="mb-20">
          <div className="grid md:grid-cols-3 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl font-bold text-{{ website.color_scheme }}-600 mb-2">
                  {stat.value}
                </div>
                <div className="text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Team */}
        {team.length > 0 && (
          <div>
            <h3 className="text-3xl font-bold text-center mb-12">Meet Our Team</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {team.map((member, index) => (
                <Card key={index} className="text-center">
                  <CardHeader>
                    <div className="w-24 h-24 bg-{{ website.color_scheme }}-100 rounded-full mx-auto mb-4" />
                    <CardTitle>{member.name}</CardTitle>
                    <CardDescription>{member.role}</CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

export default About