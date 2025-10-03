## Daniel & Kelly’s Extraordinary Universe — Brand Guide

### 1) Mission (for metadata, hero, PR)
- One-liner: Exploring imagination in the age of AI.
- Blurb (2–3 sentences): Daniel & Kelly’s Extraordinary Universe explores the future of AI and human imagination—through stories, voices, and ideas that connect us all. A local-first search engine turns conversations into a living library, so anyone can discover, learn, and collaborate.

### 2) Typography
- Headlines: Inter (700/600). Modern, confident; tight leading on large sizes.
- Body: Merriweather (300/400). Humanist warmth, generous line-height for readability.
- Scale: 12, 14, 16, 18, 24, 32, 48 (mobile-first). Line-height ~1.4–1.6 for body.
- Usage: H1 bold, H2–H3 600, body 400, microcopy 300.

### 3) Color Palette
- Primary (Electric Cyan): #00E6FF
- Accent (Cosmic Violet): #7A4FFF
- Background (Deep Space Navy): #0B1D3A
- Surface (Panels): #0F2448 / Elevated #132A52
- Text Primary: #FFFFFF, Text Secondary: #C5D0EA, Muted: #8BA1C7
- Borders: #1E3A6B / #254476
- Light-mode surfaces auto-derive via prefers-color-scheme.

### 4) Iconography & Marks
- Favicon: Cyan→Navy radial with subtle orbital lines (inline SVG embedded in <head>).
- Brand Mark: Circular gradient orb (Cyan↔Violet) with soft inner glow.
- Line icons: 2px stroke, rounded caps, subtle glow on hover for interactive states.

### 5) Imagery
- Hero: Abstract cosmic gradient with faint stars or generative nebula imagery.
- Support: Subtle line illustrations (constellations, idea graphs), blurred gradient overlays.
- Direction: Curated, no stock clip art. High contrast against dark backgrounds.

### 6) Layout & Grid
- Container width: 1200px max, 1rem horizontal padding.
- Grid gap: 2rem. Generous white space for premium feel.
- Sections: Hero → About → How It Works → Episodes/Search → Future Vision → Footer.

### 7) Motion & Micro-Interactions
- Underline reveal: Gradient underline animates on load (800ms, ease).
- Starfield: Lightweight canvas stars drifting subtly; opacity ≤ 0.6.
- Buttons: 1–2px translate on hover; no aggressive scaling.
- Scroll: Smooth anchors, sticky nav with active link highlighting.

### 8) Accessibility
- Contrast: Headline/body ≥ WCAG AA against dark surfaces.
- Focus states: Visible focus ring for interactive elements.
- Semantics: Landmarks (header, nav, sections with aria-label, footer), logical heading order.
- Motion: Keep subtle; avoid parallax tied to scroll position.

### 9) Components (baseline)
- Navigation: Sticky, glassy backdrop, 3–4 links (About, Episodes, Search, Contact).
- Hero: H1 + subhead + primary/secondary CTAs; starfield background.
- Stats: Episodes, Chunks, Index status.
- Search: Central input, glowing focus, curated episode cards with score chips and metadata.
- Cards: 12–16px radius, 1px borders, soft gradient thumbnails when images missing.

### 10) Content Voice
- Tone: Clear, inspiring, credible. Short, strong statements; avoid jargon.
- Examples: “Search the Universe”, “Discover Episodes”, “How it Works”.

### 11) Engineering Notes
- CSS variables define the theme; dark/light via prefers-color-scheme.
- Fonts loaded from Google Fonts; consider self-hosting for production.
- Keep JS lightweight; animations GPU-friendly; no heavy libraries.

### 12) Extensions (Roadmap)
- Episode browser with thumbnails and summaries; curated themes.
- Partner/investor page with vision and roadmap visuals.
- Analytics for search terms, engagement; iterate on messaging clarity.


