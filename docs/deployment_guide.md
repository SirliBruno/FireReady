# Deployment and reliable local demonstration

The application is static: browser-side solvers and versioned JSON assets require no API secrets or backend. No hosting target or hosting credentials are configured in this checkout; the GitHub remote is a source repository, not evidence of a live deployment. No remote deployment has been performed in this sprint.

## Local production demo

```powershell
npm ci
npm run build
npm run preview -- --port 4185
```

Open `http://127.0.0.1:4185/#presentation` or `/#simulator`. Routes use URL hashes, so refreshing a hash route serves index.html. To test the build through its own preview server (port 4185 must be free):

```powershell
npx playwright test --config playwright.production.config.ts --reporter=line
```

The resource simulator defaults to the included verified local boundary and processed geometry; it does not require external tiles. The optional road basemap and other satellite-exploration map backgrounds need internet. The four IBM Plex Sans Arabic weights are included locally with their SIL Open Font License, with a system fallback. This is a local-server fallback, not a service worker or a guarantee of offline first navigation to a remote site. OpenStreetMap road imagery is not used for routing costs.

## Static host

Use build command `npm run build`, output directory `dist`, Node version compatible with the lockfile (current local build verified). Upload all of `dist`, including `data/`. Preview it before sharing. Vercel/Netlify/static file hosting at the domain root can serve this output directly. No authentication/environment variables are required.

For a project subpath such as GitHub Pages, build with `npx vite build --base=/FireReady/` and publish `dist`. That subpath deployment has not been verified here. Do not upload `data/raw`, `.venv`, local development files or secrets. Only public, user-authorized research exports and government geographic assets are bundled.

Rebuilding scientific planning data additionally requires the prior frozen local pipeline inputs; running the frontend does not. Source-data limitations are documented in `docs/scientific_claims.md`.
