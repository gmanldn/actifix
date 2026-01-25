#!/usr/bin/env bash

# This script applies a clean, modern portal theme to the Actifix front‑end.
# It introduces an Azure‑inspired colour palette and adjusts the layout to
# feel brighter and more corporate. The theme is activated via the
# data‑theme="portal" attribute on the <body> element. Running this script
# is idempotent: subsequent executions will not duplicate theme definitions
# or attributes.

set -euo pipefail

# Define paths to the front‑end assets relative to the repository root.
FRONTEND_DIR="actifix-frontend"
CSS_FILE="$FRONTEND_DIR/styles.css"
INDEX_FILE="$FRONTEND_DIR/index.html"

# Append the portal theme CSS if it hasn't already been added. The
# presence of "data-theme=\"portal\"" in the stylesheet acts as a sentinel.
if ! grep -q 'data-theme="portal"' "$CSS_FILE"; then
  cat >> "$CSS_FILE" <<'PORTAL_CSS'

/* =====================================================================
 * Portal Light Theme – Azure‑inspired (added by apply_portal_theme.sh)
 *
 * This theme transforms the existing dark UI into a clean and modern
 * interface reminiscent of the Microsoft Azure portal. Colours are
 * light and neutral with a bold azure accent, panels are white with
 * subtle shadows, and the header and navigation are clearly defined.
 */

[data-theme="portal"] {
  /* Base colours */
  --bg-primary: #f5f5f5;          /* page background */
  --bg-secondary: #ffffff;        /* panels and nav rail */
  --bg-panel: #ffffff;            /* metric tiles */
  --bg-panel-hover: #f0f8ff;      /* hover state for tiles */
  --accent: #0078d4;              /* primary azure accent */
  --accent-soft: rgba(0, 120, 212, 0.1); /* subtle accent for hovers */
  --accent-muted: #0a62a4;        /* darker accent for borders/indicators */
  --text-primary: #0f1a2d;        /* dark text */
  --text-muted: #4b5563;          /* medium text */
  --text-dim: #6b7280;            /* dim text */
  --border: rgba(0, 0, 0, 0.08);  /* light borders */
  --border-hover: rgba(0, 0, 0, 0.15);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.07);
  --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.12);
}

/* Override the body background and font for the portal theme. Without
 * this override the default dashboard uses a dark radial gradient. We
 * choose a simple light gradient and use Segoe UI to mirror Azure’s
 * typographic choices. */
[data-theme="portal"] body {
  background: linear-gradient(180deg, #f5f5f5 0%, #ffffff 100%);
  font-family: 'Segoe UI', Tahoma, sans-serif;
}

/* Header adopts the accent colour and white text */
[data-theme="portal"] .dashboard-header {
  background: var(--accent);
  color: #ffffff;
  border-bottom: none;
}
[data-theme="portal"] .dashboard-header .header-title h1,
[data-theme="portal"] .dashboard-header .header-subtitle,
[data-theme="portal"] .dashboard-header .header-time,
[data-theme="portal"] .dashboard-header .connection-status {
  color: #ffffff;
}
[data-theme="portal"] .connection-status {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.25);
}

/* Navigation rail is white with azure highlights */
[data-theme="portal"] .nav-rail {
  background: var(--bg-secondary);
  border-right: 1px solid #d0d7de;
}
[data-theme="portal"] .nav-rail-item {
  color: #4b5563;
}
[data-theme="portal"] .nav-rail-item:hover {
  background: var(--accent-soft);
  color: var(--accent);
}
[data-theme="portal"] .nav-rail-item.active {
  background: var(--accent);
  color: #ffffff;
}

/* Tiles adopt a white background with subtle shadows */
[data-theme="portal"] .metric-tile {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
}

/* Buttons use the accent colour with white text */
[data-theme="portal"] .fix-button {
  background: var(--accent);
  color: #ffffff;
}
[data-theme="portal"] .fix-button:hover {
  background: #005ea2; /* darker azure on hover */
}

PORTAL_CSS
fi

# Modify the body tag to enable the portal theme globally. Only perform
# substitution if no data-theme is currently set on the body element.
if ! grep -q 'data-theme=' "$INDEX_FILE"; then
  # Use sed to insert the data-theme attribute on the <body> tag
  sed -i '' 's/<body>/<body data-theme="portal">/' "$INDEX_FILE"
fi

echo "Portal theme applied successfully."