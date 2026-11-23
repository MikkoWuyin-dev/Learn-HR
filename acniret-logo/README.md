# ACNIRET Care — logo assets

Pulled from <https://acniret.com/> on 2026-11-23.

## What the site actually serves

The site publishes **exactly one** logo lockup. It is used for the header, the
footer, and (downscaled to 64×64) the favicon:

| Asset | Original URL |
|---|---|
| Logo (header + footer) | `https://acniret.com/__l5e/assets-v1/5275e09e-f13b-4b47-aa55-7c65bca73044/acniret-care-logo.png` |
| Favicon | `https://acniret.com/favicon.png` |
| Social card (`og:image`) | `https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/lovp_6e31ejdcme9zm9dvtfj3x0ya3s/3784003d1536d5fbfb0d4fa93b4529a9_1792149081583.png` |

The master file is **1420 × 202 px, RGBA PNG, 180,326 bytes**,
SHA-256 `f40d286419507889f3709a4acf001334b1a373f8795cf7ec6518fff3aae80d9b`.

## There are no published alternates

This was verified, not assumed. Each of these returns a genuine **404**:

- `acniret-care-logo.svg`, `.webp`, `@2x.png`, `@3x.png`, `-2x.png`, `-3x.png`
- `acniret-care-logo-dark.png`, `-light.png`, `-white.png`, `-black.png`, `-alt.png`
- `acniret-care-logo-stacked.png`, `-horizontal.png`, `-square.png`
- `acniret-care-mark.png/.svg`, `acniret-care-icon.png/.svg`
- `acniret-care-wordmark.png/.svg`, `acniret-care-symbol.png`, `acniret-care-favicon.png`
- `acniret-logo.png/.svg`, `acniret-mark.png`
- `/logo.png`, `/logo.svg`, `/brand/logo.png`, `/og.png`, `/og-image.png`, `/social.png`
- `/favicon.ico`, `/favicon-16x16.png`, `/favicon-32x32.png`, `/apple-touch-icon.png`,
  `/apple-touch-icon-180x180.png`, `/apple-touch-icon-precomposed.png`, `/mstile-150x150.png`
- `/manifest.webmanifest`, `/site.webmanifest`

A full scan of every CSS/JS bundle found only one `assets-v1` reference in the
entire application — the same `acniret-care-logo.png`. There is no authored SVG,
no light/dark pair, and no monochrome mark anywhere on the site.

## Files in this folder

| File | Dimensions | Notes |
|---|---|---|
| `acniret-care-logo.png` | 1420 × 202 | **The original master.** Byte-identical to what the site serves. |
| `acniret-care-logo@2x.png` | 2840 × 404 | Upscaled from the master (Lanczos on premultiplied alpha). |
| `acniret-care-logo-white.png` | 1420 × 202 | Recoloured white, alpha preserved. For dark backgrounds. |
| `acniret-care-logo-black.png` | 1420 × 202 | Recoloured near-black, alpha preserved. For light backgrounds. |
| `acniret-care-logo-traced.svg` | vector | Auto-traced from the raster master (see caveat below). |
| `acniret-favicon-64.png` | 64 × 64 | The site's original favicon. |
| `acniret-favicon-32.png` | 32 × 32 | Derived. |
| `acniret-favicon-16.png` | 16 × 16 | Derived. |
| `acniret-social-card-1920x1080.png` | 1920 × 1080 | The site's `og:image` — a full-page screenshot, not a standalone logo. |
| `_contact-sheet.png` | — | Preview of all variants side by side. |
| `_traced-preview.png` | 1420 × 202 | Rendered preview of the traced SVG. |

### Colour

The lockup is two-tone:

- Wordmark **ACNIRET** and the dotted "A": `#3E1A0B` (deep brown)
- **Care** and the orange dots: `#F2693C` (orange)

The white and black files are flat single-colour versions of the whole lockup,
which is what a "light/dark alternate" normally means in practice.

### Caveat on the SVG

`acniret-care-logo-traced.svg` is an **auto-trace of the PNG**, not the site's
authored vector — the site does not publish one. It was rasterised back and
diffed against the master: **0.51% mismatch**. That is visually faithful at
normal sizes, but for print work at large scale, obtain the original vector
from the brand owner rather than relying on this trace.
