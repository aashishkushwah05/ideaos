# Frontend — Idea OS

React + Vite + Tailwind CSS v4 frontend for Idea OS ("Your Knowledge OS").
See the root `README.md` for setup and run instructions, and
`docs/ARCHITECTURE.md` for architecture details.

## Current state

All 8 screens (Dashboard, Library, Search, Resource Detail, Add Resource,
Categories/Platforms/Collections, Library Health, Settings) are built with
**mock data only** (`src/data/mockData.js`). There is no live connection to
the FastAPI backend yet beyond the Phase 1 `/health` check — no real save,
no real search, no AI calls. That wiring is a future phase.

## Structure

```
src/
├── assets/            Idea OS logo (processed: cropped, transparent, recolored for dark UI)
├── context/           ThemeContext (dark/light/system), ResourcesContext (mock favorite-toggle state)
├── data/mockData.js    All mock resources/categories/collections/health data
├── components/
│   ├── layout/         Sidebar, Topbar, Footer, AppLayout (route transitions)
│   ├── ui/              Reusable primitives (Button, Card, Badge, Input, Skeleton, EmptyState, ErrorState, ...)
│   └── resources/       ResourceCard, ResourceRow, FilterBar
├── pages/               One file per screen
├── hooks/useMockLoading.js   Simulates a load phase (no real API call exists yet)
└── utils/               Platform metadata, status metadata, date formatting
```

