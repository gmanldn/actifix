# Actifix Frontend (Static React)

Minimal React-on-CDN page to mirror the Pokertool-style architecture without poker features. The page renders a black background, striking gold headline, and a small pangolin illustration.

## Usage

```bash
cd actifix-frontend
python3 -m http.server 8080
```

Open http://localhost:8080 to view the page. No build step is required; React and ReactDOM are pulled via CDN.

## Behavior
- Full-width headline: `Love Actifix - Always Bitches!!!`
- Black background, gold typography, responsive layout
- Pangolin SVG asset in `assets/pangolin.svg`

## Notes
- No poker-specific code or endpoints are included.
- If you prefer bundling, you can wrap this structure in Vite/webpack later; the source files are already split into `index.html`, `app.js`, and `styles.css`.
