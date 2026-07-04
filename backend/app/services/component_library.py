"""
Vetted component library for structural section redesigns.

When the edit analysis detects a structural rewrite ("turn this into a
carousel", "make these tabs"), the matched entries' snippet code is injected
into the edit prompt as an adapt-this-pattern reference, which sharply cuts
hallucinated-API risk. Each entry declares the npm dependencies it needs so
the router can merge them into the generated project's package.json before
the preview rebuild (the rebuild runs npm install).
"""

import json
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LibraryComponent:
    def __init__(self, name: str, keywords: List[str], description: str,
                 snippet: str, npm_dependencies: Optional[Dict[str, str]] = None):
        self.name = name
        self.keywords = keywords
        self.description = description
        self.snippet = snippet
        self.npm_dependencies = npm_dependencies or {}


COMPONENT_LIBRARY: List[LibraryComponent] = [
    LibraryComponent(
        name="carousel",
        keywords=["carousel", "slider", "slideshow", "swiper", "image slider", "gallery slider"],
        description="Auto-scrollable image/content carousel (embla-carousel-react)",
        npm_dependencies={"embla-carousel-react": "^8.5.1"},
        snippet="""import useEmblaCarousel from 'embla-carousel-react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useCallback } from 'react';

// Inside your component:
const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true });
const scrollPrev = useCallback(() => emblaApi?.scrollPrev(), [emblaApi]);
const scrollNext = useCallback(() => emblaApi?.scrollNext(), [emblaApi]);

// JSX pattern:
<div className="relative">
  <div className="overflow-hidden" ref={emblaRef}>
    <div className="flex">
      {slides.map((slide, index) => (
        <div key={index} className="flex-[0_0_100%] min-w-0">
          <img src={slide.src} alt={slide.alt} className="w-full h-96 object-cover" />
        </div>
      ))}
    </div>
  </div>
  <button onClick={scrollPrev} aria-label="Previous slide"
    className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full p-2 shadow">
    <ChevronLeft className="w-5 h-5" />
  </button>
  <button onClick={scrollNext} aria-label="Next slide"
    className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full p-2 shadow">
    <ChevronRight className="w-5 h-5" />
  </button>
</div>""",
    ),
    LibraryComponent(
        name="testimonial-slider",
        keywords=["testimonial slider", "testimonial carousel", "reviews slider", "quotes carousel"],
        description="Sliding testimonials with author info (embla-carousel-react)",
        npm_dependencies={"embla-carousel-react": "^8.5.1"},
        snippet="""import useEmblaCarousel from 'embla-carousel-react';

const [emblaRef] = useEmblaCarousel({ loop: true, align: 'start' });

<div className="overflow-hidden" ref={emblaRef}>
  <div className="flex gap-6">
    {testimonials.map((t, index) => (
      <div key={index} className="flex-[0_0_100%] md:flex-[0_0_45%] min-w-0 bg-white rounded-xl p-6 shadow">
        <p className="text-gray-700 italic">"{t.quote}"</p>
        <div className="mt-4 flex items-center gap-3">
          <img src={t.avatar} alt={t.author} className="w-10 h-10 rounded-full object-cover" />
          <div>
            <p className="font-semibold">{t.author}</p>
            <p className="text-sm text-gray-500">{t.role}</p>
          </div>
        </div>
      </div>
    ))}
  </div>
</div>""",
    ),
    LibraryComponent(
        name="tabs",
        keywords=["tabs", "tabbed", "tab panel", "switch between"],
        description="Tabbed content (shadcn/ui Tabs — already available at @/components/ui/tabs)",
        snippet="""import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

<Tabs defaultValue="first" className="w-full">
  <TabsList>
    <TabsTrigger value="first">First</TabsTrigger>
    <TabsTrigger value="second">Second</TabsTrigger>
  </TabsList>
  <TabsContent value="first">First tab content</TabsContent>
  <TabsContent value="second">Second tab content</TabsContent>
</Tabs>""",
    ),
    LibraryComponent(
        name="accordion",
        keywords=["accordion", "faq", "expandable", "collapsible", "frequently asked"],
        description="Expandable accordion / FAQ list (shadcn/ui Accordion — already available at @/components/ui/accordion)",
        snippet="""import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';

<Accordion type="single" collapsible className="w-full">
  {items.map((item, index) => (
    <AccordionItem key={index} value={`item-${index}`}>
      <AccordionTrigger>{item.question}</AccordionTrigger>
      <AccordionContent>{item.answer}</AccordionContent>
    </AccordionItem>
  ))}
</Accordion>""",
    ),
    LibraryComponent(
        name="video-embed",
        keywords=["video", "youtube", "vimeo", "embed video", "video background"],
        description="Responsive video embed (iframe, no dependencies)",
        snippet="""<div className="relative w-full overflow-hidden rounded-xl" style={{ paddingBottom: '56.25%' }}>
  <iframe
    src="https://www.youtube.com/embed/VIDEO_ID"
    title="Video"
    className="absolute inset-0 w-full h-full"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowFullScreen
  />
</div>""",
    ),
    LibraryComponent(
        name="pricing-table",
        keywords=["pricing", "price table", "plans", "tiers", "subscription plans"],
        description="Three-tier pricing table with highlighted plan (no dependencies)",
        snippet="""<div className="grid md:grid-cols-3 gap-8">
  {plans.map((plan, index) => (
    <div key={index}
      className={`rounded-2xl p-8 border ${plan.featured ? 'border-primary shadow-xl scale-105 bg-white' : 'border-gray-200 bg-white/60'}`}>
      <h3 className="text-lg font-semibold">{plan.name}</h3>
      <p className="mt-2 text-4xl font-bold">{plan.price}<span className="text-base font-normal text-gray-500">/mo</span></p>
      <ul className="mt-6 space-y-3">
        {plan.features.map((feature, i) => (
          <li key={i} className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" />{feature}</li>
        ))}
      </ul>
      <button className={`mt-8 w-full rounded-lg py-2.5 font-medium ${plan.featured ? 'bg-primary text-white' : 'border border-gray-300'}`}>
        {plan.cta}
      </button>
    </div>
  ))}
</div>""",
    ),
    LibraryComponent(
        name="stats-grid",
        keywords=["stats", "statistics", "numbers", "counters", "metrics"],
        description="Stat/metric grid (no dependencies)",
        snippet="""<div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
  {stats.map((stat, index) => (
    <div key={index}>
      <p className="text-4xl font-bold text-primary">{stat.value}</p>
      <p className="mt-1 text-sm text-gray-500">{stat.label}</p>
    </div>
  ))}
</div>""",
    ),
]

_BY_NAME = {c.name: c for c in COMPONENT_LIBRARY}


def match_components(suggested: Optional[List[str]], instruction: str) -> List[LibraryComponent]:
    """Match analysis suggestions (and the raw instruction) to library entries."""
    matched: Dict[str, LibraryComponent] = {}

    for name in suggested or []:
        normalized = str(name).strip().lower().replace(" ", "-")
        if normalized in _BY_NAME:
            matched[normalized] = _BY_NAME[normalized]
            continue
        # loose keyword match on the suggestion text
        for component in COMPONENT_LIBRARY:
            if any(k in str(name).lower() for k in component.keywords):
                matched[component.name] = component

    instruction_lower = instruction.lower()
    for component in COMPONENT_LIBRARY:
        if any(k in instruction_lower for k in component.keywords):
            matched[component.name] = component

    return list(matched.values())


def build_library_note(components: List[LibraryComponent]) -> Optional[str]:
    """Prompt block presenting vetted patterns the rewrite should adapt."""
    if not components:
        return None
    blocks = []
    for c in components:
        dep_note = ""
        if c.npm_dependencies:
            dep_note = f" (dependencies {', '.join(c.npm_dependencies)} are installed — import them exactly as shown)"
        blocks.append(f"### {c.name}: {c.description}{dep_note}\n```tsx\n{c.snippet}\n```")
    return (
        "VETTED COMPONENT PATTERNS — adapt these exact patterns instead of inventing APIs; "
        "keep imports as shown and adjust content/styling to fit the site:\n\n"
        + "\n\n".join(blocks)
    )


def collect_dependencies(components: List[LibraryComponent]) -> Dict[str, str]:
    deps: Dict[str, str] = {}
    for c in components:
        deps.update(c.npm_dependencies)
    return deps


def ensure_package_dependencies(package_json_content: str, deps: Dict[str, str]) -> Optional[str]:
    """Merge missing deps into package.json content; None if nothing to add."""
    if not deps:
        return None
    try:
        package = json.loads(package_json_content)
    except json.JSONDecodeError:
        logger.warning("[COMPONENT LIBRARY] package.json is not valid JSON; skipping dependency merge")
        return None
    dependencies = package.setdefault("dependencies", {})
    missing = {name: version for name, version in deps.items() if name not in dependencies}
    if not missing:
        return None
    dependencies.update(missing)
    logger.info(f"[COMPONENT LIBRARY] Adding dependencies to package.json: {list(missing)}")
    return json.dumps(package, indent=2)
