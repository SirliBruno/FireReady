# Sprint 01 report — foundation in progress

## Implemented
- Introductory landing experience, seven analytical routes and a guided presentation route, responsive shell, keyboard focus, reduced-motion CSS, error boundary and no-data states.
- Shared MapLibre Maui map on the introduction and Command Center, with zoom, pan, reset, fullscreen, layer availability, attribution, resize handling and network error notice. Basemap: OpenFreeMap Liberty. Screenshot samples: [landing](screenshots/landing-new.png), [synthetic seasonal view](screenshots/synthetic-new.png), [mobile](screenshots/landing-mobile.png).
- Explicit synthetic preview from an isolated reproducible fixture; persistent global and chart labels. Seasonal monthly bars are calculated from validated data, with a year selector. Missing months are not assumed to be zero.
- Zod validation and a static monthly-aggregate data repository: default awaiting-data mode, explicit synthetic mode, and a reviewed real-data path requiring metadata and a review assertion. Validation cannot authenticate the source or prove scientific validity. No real data has been supplied. Consult `docs/data_contracts.md` before publishing any data.
- Simulator scenario input/reset with an explicitly disabled solver; scientific methods and limitations labelled as planned. Typed initial contracts and source documentation.

## Verification
- Installation: `npm install zod --prefer-offline --fetch-retries=2 --fetch-timeout=120000 --no-audit --no-fund` succeeded. Dependency lockfile updated.
- `npm run typecheck`: passed.
- `npm run lint`: passed.
- `npm test`: passed, 7 tests in 2 files.
- `npm run build`: passed. Rollup warns about Zod comment annotations and a large 1.81 MB JS chunk (509 kB gzip); code splitting is recommended.
- `npx playwright test`: 23 passed using installed Microsoft Edge. Tests include nine routes, 1920/1440/1024/768/390 horizontal overflow, scenario reset, dataset labeling and malformed data, basic keyboard focus, reduced-motion preference, uncaught page errors, map-service failure, and presentation navigation. This is not a complete accessibility or console/network audit.
- Browser screenshots were captured and visually inspected for landing, synthetic seasonal chart, and mobile. A map resize issue and a landing rendering issue were fixed, then rechecked.

## Outstanding work and limitations
Sprint 01 is **not fully complete** against the supplied specification. GeoJSON observation and station layers, feature hover/selection, dynamic legends, synchronized sensor maps, temporal and geographic selection, full station inventory, comparison maps, comprehensive Maui 2023 scrollytelling and official findings, and several scientific data contracts remain unimplemented. There is no CSV pipeline, harmonization algorithm, travel network, optimizer, coverage analysis or scientific evaluation. Map layer toggles are disabled with explanations. There is no full presentation-mode overlay or notification system. Some UI components remain centralized in `App.tsx`. The current map style is light; it needs a suitable dark style. Only the monthly aggregate format is wired to the repository; the draft JSON schemas and more general TypeScript interfaces are not a full import implementation.

Synthetic values are invented and not NASA records. Human review metadata is an assertion and cannot establish authenticity. NASA FIRMS and auxiliary datasets, sources for station inventories, and validated real scientific results remain unavailable. No claim is made that historical observations predict fire probability or that the system could have prevented the Maui tragedy.

## Sources, assumptions and next work
The challenge description was cross-checked against the official Space Apps team page: https://www.spaceappschallenge.org/2026/find-a-team/the-one2/ . The full challenge page could not be reliably retrieved; check full official requirements and event-specific submissions. The official investigation resource is https://ag.hawaii.gov/maui-wildfire-investigation-resources-page/ . OpenFreeMap describes its style and attribution at https://openfreemap.org/quick_start/ ; network availability is not guaranteed.

Before scientific implementation, acquire and independently verify sources, implement complete schemas and spatial adapters, assess sensor matching and uncertainty, and separate training (2013–2020), validation (2021–2022), and held-out testing (2023). Do not tune on August 2023. For local development run `npm install` and `npm run dev`.
