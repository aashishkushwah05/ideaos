# Phase 13 — Mobile Web Experience & PWA Foundation

Phase 13 keeps IdeaOS web-first. Native Android remains frozen for a later phase.

## Implemented
- Responsive mobile navigation with bottom navigation and safe-area support.
- Mobile-friendly spacing and form sizing to avoid browser zoom on iOS.
- Installable PWA manifest.
- Production service-worker shell/fallback.
- Web Share Target capture flow at `/share`.
- Shared URL/text is sent through the existing backend resource pipeline; no provider credentials are exposed to the browser.
- Share capture supports duplicate detection and opens the saved resource when available.
- Desktop sidebar/topbar remain unchanged in large layouts.

## Explicit non-goals
- No native Android feature development.
- No cloud sync.
- No client-side AI provider credentials.
- No replacement of the existing backend API with browser-direct provider calls.

## Verification
Backend regression tests should be run with `python -m pytest -q`.
Frontend build/lint should be run on the user's Windows environment because package installation/build was not reliable in the isolated build environment.
