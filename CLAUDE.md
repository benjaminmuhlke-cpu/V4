# 楞先生 — Outdoor & Technical Clothing Store

## Project Overview
One-page website for **楞先生**, a family-owned outdoor and technical clothing store with 25+ years of experience. All content is in **Traditional Chinese (Mandarin)**.

## Tech Stack
- **React** + **TypeScript**
- **Vite** (build tool, base path set to `/V4/` for GitHub Pages)
- **Tailwind CSS** (custom earthy color palette)
- **Google Fonts**: Playfair Display (headings) + Source Sans 3 (body)

## Deployment
- **GitHub Pages** via GitHub Actions workflow (`.github/workflows/deploy.yml`)
- Live URL: `https://benjaminmuhlke-cpu.github.io/V4/`
- Push to `main` → auto-deploys

## Design
- **Style**: Earthy & rugged
- **Palette**: deep earth dark `#1C1208`, forest green `#2C4A2E`, amber `#C67B2E`, cream `#F4EDE0`
- **Logo**: Wood-carved sign SVG at `public/logo.svg` (replace with `public/logo.png` for the real photo)

## Page Structure (`src/sections/`)
| File | Section |
|------|---------|
| `HeroSection.tsx` | Full-screen hero with CSS gradient + logo + tagline |
| `StorySection.tsx` | Dark section with stats (25+, 100%) and store story |
| `BrandsSection.tsx` | Grid of 25 brands with logos (via Clearbit API) + hover effect |
| `FooterSection.tsx` | Dark footer with logo and tagline |

## Brands Carried
Ecco, Aigle, Smartwool, Montbell, Lafuma, Marmot, Icebreaker, TBS, Prana, GoLite, Fusalp, Cloudveil, Gregory, Coleman, Gore-Tex, Wigwam, Keen, Stanley, Nalgene, Ziener, Buff, Black Diamond, CamelBak, Chaco, Oofos

## Store Story (for copy reference)
- Family-owned, 25+ years
- Every brand personally tested across all weather/conditions
- "Come with a challenge, leave fully equipped" — 帶著挑戰而來，全副武裝而歸

## Dev Commands
```bash
npm run dev      # local dev server
npm run build    # production build
```
