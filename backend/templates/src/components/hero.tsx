import { Button } from "@/components/ui/button"
import { ArrowRight, Play } from "lucide-react"

interface HeroProps {
  title?: string
  subtitle?: string
  description?: string
  primaryAction?: string
  secondaryAction?: string
  image?: string
  video?: string
}

const Hero = ({ 
  title = "{{ component.content.title or 'Welcome to ' + website.title }}",
  subtitle = "{{ component.content.subtitle or website.description }}",
  description = "{{ component.content.description or 'Build amazing experiences with our platform' }}",
  primaryAction = "Get Started",
  secondaryAction = "Learn More",
  image,
  video
}: HeroProps) => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 z-0">
        {video ? (
          <video 
            className="w-full h-full object-cover"
            autoPlay 
            muted 
            loop
            playsInline
          >
            <source src={video} type="video/mp4" />
          </video>
        ) : (
          <div 
            className="w-full h-full bg-gradient-to-br from-{{ website.color_scheme }}-500 to-{{ website.color_scheme }}-700"
            style={{
              backgroundImage: image ? `url(${image})` : undefined,
              backgroundSize: 'cover',
              backgroundPosition: 'center'
            }}
          />
        )}
        <div className="absolute inset-0 bg-black/40" />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold text-white mb-6">
            {title}
          </h1>
          <p className="text-xl sm:text-2xl text-white/90 mb-8">
            {subtitle}
          </p>
          <p className="text-lg text-white/80 mb-12 max-w-2xl mx-auto">
            {description}
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg" 
              className="bg-white text-{{ website.color_scheme }}-600 hover:bg-white/90"
            >
              {primaryAction}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              className="border-white text-white hover:bg-white hover:text-{{ website.color_scheme }}-600"
            >
              {video ? <Play className="mr-2 h-4 w-4" /> : null}
              {secondaryAction}
            </Button>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10">
        <div className="w-6 h-10 border-2 border-white/50 rounded-full flex justify-center">
          <div className="w-1 h-3 bg-white/50 rounded-full mt-2 animate-bounce" />
        </div>
      </div>
    </section>
  )
}

export default Hero