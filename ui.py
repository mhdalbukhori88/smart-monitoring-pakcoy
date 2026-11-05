"""Komponen tampilan profesional (CSS, kartu KPI, banner, SVG icons) untuk Smart Farming Pakcoy.
Sistem desain Agronomi & Precision Agriculture bertema Hijau Pakcoy (Botanical Green)."""
import base64
import html
import re
from pathlib import Path
import streamlit as st

# Regex lengkap untuk mendeteksi karakter emoji dan simbol grafis
EMOJI_REGEX = re.compile(
    r"[\U0001F000-\U0001FAFF"
    r"\u2600-\u27BF"
    r"\u2B00-\u2BFF"
    r"\uFE00-\uFE0F"
    r"\u200D"
    r"\u20E3"
    r"\u2190-\u21FF"
    r"\u2300-\u23FF"
    r"✅❌⚠️⚠▶⏸✓🔥💧🌡🌱📈🤖🗓📄🔍📉⚡🎯🧺🌿🧱📐🍃🎨↔📏🔮🖼🏠📊📡🧠📅📸⬇🥬⏰📍ℹ⛔💡]+",
    flags=re.UNICODE
)


def strip_emoji(text):
    """Menghapus karakter emoji dan simbol untuk tampilan teks profesional."""
    cleaned = EMOJI_REGEX.sub("", str(text))
    return re.sub(r"\s+", " ", cleaned).strip()


# Koleksi SVG Line Icons (Gaya Lucide/Feather, stroke-width 1.75, round cap/join)
ICONS = {
    "sprout": '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4.1 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    "layout-dashboard": '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
    "bar-chart-3": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "cpu": '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
    "calendar-range": '<rect width="18" height="18" x="3" y="4" rx="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/><path d="M17 14h-6"/><path d="M13 18H7"/><path d="M7 14h.01"/><path d="M17 18h.01"/>',
    "scan-line": '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/>',
    "scan-search": '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><circle cx="12" cy="12" r="3"/><path d="m16 16-1.9-1.9"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>',
    "droplets": '<path d="M7 16.3c2.2 0 4-1.83 4-4.05 0-1.16-.57-2.26-1.71-3.19S7.29 6.75 7 5.3c-.29 1.45-1.14 2.84-2.29 3.76S3 11.1 3 12.25c0 2.22 1.8 4.05 4 4.05z"/><path d="M12.56 6.6A10.97 10.97 0 0 0 14 3.02c.5 2.5 2 4.9 4 6.5s3 3.5 3 5.5a6.98 6.98 0 0 1-11.91 4.97"/>',
    "thermometer": '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
    "trending-up": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "trending-down": '<polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/>',
    "calendar": '<rect width="18" height="18" x="3" y="4" rx="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/>',
    "refresh-cw": '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
    "play": '<polygon points="6 3 20 12 6 21 6 3"/>',
    "alert-triangle": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "x-circle": '<circle cx="12" cy="12" r="10"/><line x1="15" x2="9" y1="9" y2="15"/><line x1="9" x2="15" y1="9" y2="15"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    # Ganti ikon sparkles AI menjadi ikon presisi target/akurasi ilmiah
    "sparkles": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "maximize": '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>',
    "sliders": '<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/>',
    "camera": '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
    "message-square": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "user-plus": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="11" cy="7" r="4"/><line x1="19" x2="19" y1="8" y2="14"/><line x1="22" x2="16" y1="11" y2="11"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "log-out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/><path d="M19 3v4"/><path d="M21 5h-4"/>'
}

ICON_MAP = {
    "📄": "database", "💧": "droplets", "🌡️": "thermometer", "🌡": "thermometer",
    "📈": "trending-up", "🗓️": "calendar", "🗓": "calendar", "🤖": "cpu",
    "🌱": "sprout", "⚡": "zap", "📉": "activity", "🎯": "sparkles",
    "✅": "check-circle", "🧺": "layers", "🌿": "sprout", "🧱": "layers",
    "📐": "maximize", "🍃": "sprout", "🎨": "sparkles", "📏": "maximize",
    "↔️": "maximize", "↔": "maximize", "📅": "calendar", "🔍": "scan-search"
}


def icon(name, size=18, color="currentColor"):
    """Mengembalikan inline SVG line icon (viewBox 24x24, stroke 1.75)."""
    inner = ICONS.get(name, ICONS.get(ICON_MAP.get(name, "sprout"), ICONS["sprout"]))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" '
        f'stroke-linecap="round" stroke-linejoin="round" class="ui-svg-icon">{inner}</svg>'
    )


_LOGO_B64_CACHE = None


def brand_logo_html(size=34):
    """Mengembalikan tag <img> base64 untuk logo Pakcoy di assets/logo_pakcoy.png."""
    global _LOGO_B64_CACHE
    if _LOGO_B64_CACHE is None:
        logo_path = Path(__file__).parent / "assets" / "logo_pakcoy.png"
        if logo_path.exists():
            _LOGO_B64_CACHE = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        else:
            _LOGO_B64_CACHE = ""
    if _LOGO_B64_CACHE:
        return (
            f'<img src="data:image/png;base64,{_LOGO_B64_CACHE}" '
            f'width="{size}" height="{size}" '
            f'style="width:{size}px;height:{size}px;object-fit:contain;display:block;" '
            f'alt="Logo Smart Farming Pakcoy"/>'
        )
    return icon("sprout", size, color="#15803d")


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

:root {
  --primary: #15803d;
  --primary-deep: #166534;
  --primary-press: #14532d;
  --primary-soft: #16a34a;
  --primary-subdued: #f0fdf4;
  --primary-bg-subdued-hover: #dcfce7;
  --brand-dark-900: #052e16;
  --ink: #111c16;
  --ink-secondary: #2c3e35;
  --ink-mute: #5c6f64;
  --ink-mute-2: #6b7f73;
  --on-primary: #ffffff;
  --canvas: #ffffff;
  --canvas-soft: #f6f8f6;
  --canvas-cream: #f1f5f2;
  --hairline: #dce5de;
  --hairline-input: #b8c9be;
  --ruby: #dc2626;
  --magenta: #15803d;
  --lemon: #d97706;
  --shadow-blue: #14532d;
  --success: #15803d;
  --success-bg: #f0fdf4;
  --warning: #b45309;
  --warning-bg: #fffbeb;
  --danger: #dc2626;
  --danger-bg: #fef2f2;
  --info: #166534;
  --info-bg: #f0fdf4;
  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 10px;
  --radius-xl: 12px;
  --radius-pill: 8px;
}

/* Global App Styling */
html, body, [class*="css"], .stApp {
  font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  color: var(--ink);
  background-color: var(--canvas-soft);
}

.block-container {
  padding-top: 1.4rem !important;
  padding-bottom: 2.8rem !important;
  padding-left: 2.2rem !important;
  padding-right: 2.2rem !important;
  max-width: 1440px !important;
}

/* Styled Bordered Containers (Toolbar / Filter Cards) */
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlockBorderWrapper"] {
  background-color: #ffffff !important;
  border: 1px solid #dce5de !important;
  border-radius: 10px !important;
  padding: 14px 18px !important;
  box-shadow: 0 1px 2px rgba(17, 28, 22, 0.03) !important;
}

/* Hide Default Streamlit Chrome */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

header[data-testid="stHeader"] {
  background: transparent !important;
  z-index: 99 !important;
}

/* Floating Sidebar Reopen / Expand Button (Saat Sidebar Tertutup) */
[data-testid="stExpandSidebarButton"],
[data-testid="stExpandSidebarButton"] button,
button[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
header[data-testid="stHeader"] button[aria-label="Expand sidebar"] {
  display: flex !important;
  visibility: visible !important;
  position: fixed !important;
  top: 14px !important;
  left: 14px !important;
  z-index: 999999 !important;
  width: 38px !important;
  height: 38px !important;
  min-width: 38px !important;
  min-height: 38px !important;
  align-items: center !important;
  justify-content: center !important;
  background-color: #ffffff !important;
  color: #15803d !important;
  border: 1px solid #dce5de !important;
  border-radius: 8px !important;
  box-shadow: 0 2px 8px rgba(17, 28, 22, 0.08) !important;
  cursor: pointer !important;
  transition: all 0.18s ease !important;
  margin: 0 !important;
  padding: 0 !important;
  outline: none !important;
}

[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stExpandSidebarButton"] button:hover,
button[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover,
[data-testid="collapsedControl"]:hover,
header[data-testid="stHeader"] button[aria-label="Expand sidebar"]:hover {
  background-color: #f0fdf4 !important;
  border-color: #86efac !important;
  color: #14532d !important;
  box-shadow: 0 4px 12px rgba(21, 128, 61, 0.14) !important;
}

[data-testid="stExpandSidebarButton"] svg,
[data-testid="stExpandSidebarButton"] span,
button[data-testid="stExpandSidebarButton"] svg,
button[data-testid="stExpandSidebarButton"] span {
  color: inherit !important;
  fill: currentColor !important;
}

/* Sidebar Container saat Terbuka (Expanded) */
section[data-testid="stSidebar"]:not([data-collapsed="true"]):not([aria-expanded="false"]),
[data-testid="stSidebar"]:not([data-collapsed="true"]):not([aria-expanded="false"]) {
  background-color: #ffffff !important;
  border-right: 1px solid #dce5de !important;
  width: 280px !important;
  min-width: 280px !important;
  max-width: 280px !important;
  transform: none !important;
  visibility: visible !important;
  box-shadow: 1px 0 8px rgba(17, 28, 22, 0.03) !important;
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), width 0.25s ease !important;
  z-index: 100 !important;
}

/* Sidebar Container saat Tertutup (Collapsed) */
section[data-testid="stSidebar"][data-collapsed="true"],
[data-testid="stSidebar"][data-collapsed="true"],
section[data-testid="stSidebar"][aria-expanded="false"],
[data-testid="stSidebar"][aria-expanded="false"] {
  width: 0 !important;
  min-width: 0 !important;
  max-width: 0 !important;
  flex: 0 0 0 !important;
  border: none !important;
  border-right: none !important;
  transform: translateX(-100%) !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  visibility: hidden !important;
  box-shadow: none !important;
  pointer-events: none !important;
}

/* Sembunyikan resize handle saat sidebar tertutup */
section[data-testid="stSidebar"][data-collapsed="true"] ~ [data-testid="stSidebarResizeHandle"],
[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarResizeHandle"] {
  display: none !important;
}

/* Layout utama menyesuaikan lebar layar secara halus */
.stAppViewContainer,
[data-testid="stAppViewContainer"] {
  transition: margin-left 0.25s ease !important;
}

/* Typography: Apply Plus Jakarta Sans / Inter selectively */
[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] span:not([data-testid="stIconMaterial"]):not([class*="material"]):not([class*="Icon"]),
[data-testid="stSidebar"] div:not([data-testid="stIconMaterial"]):not([class*="material"]) {
  font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Material Symbols & Streamlit Icons MUST keep original font & ligatures */
[data-testid="stIconMaterial"],
span[class*="material"],
span[class*="Icon"],
[data-testid="stSidebar"] [data-testid="stIconMaterial"],
[data-testid="stSidebar"] span[class*="material"],
[data-testid="stSidebar"] span[class*="Icon"] {
  font-family: "Material Symbols Rounded", "Material Symbols Outlined", sans-serif !important;
  font-feature-settings: "liga" 1 !important;
  -webkit-font-feature-settings: "liga" 1 !important;
  font-variant-ligatures: normal !important;
  text-rendering: optimizeLegibility !important;
  direction: ltr !important;
  display: inline-block !important;
  line-height: 1 !important;
  font-size: 16px !important;
  letter-spacing: normal !important;
  text-transform: none !important;
  white-space: nowrap !important;
  word-wrap: normal !important;
}

/* Header Sidebar & Tombol Tutup (<<) */
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
  height: auto !important;
  min-height: 36px !important;
  padding: 8px 14px 2px 14px !important;
  margin: 0 !important;
  display: flex !important;
  justify-content: flex-end !important;
  align-items: center !important;
  background: transparent !important;
  position: static !important;
}

[data-testid="stSidebar"] button[aria-label="Collapse sidebar"],
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {
  display: inline-flex !important;
  visibility: visible !important;
  align-items: center !important;
  justify-content: center !important;
  width: 30px !important;
  height: 30px !important;
  min-width: 30px !important;
  min-height: 30px !important;
  border-radius: 6px !important;
  color: #5c6f64 !important;
  background-color: transparent !important;
  border: 1px solid transparent !important;
  box-shadow: none !important;
  cursor: pointer !important;
  padding: 0 !important;
  margin: 0 !important;
  transition: all 0.15s ease !important;
}

[data-testid="stSidebar"] button[aria-label="Collapse sidebar"]:hover,
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover,
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button:hover {
  color: #15803d !important;
  background-color: #f0fdf4 !important;
  border-color: #bbf7d0 !important;
}

/* Sidebar Scroll & Content Container */
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  padding: 0 !important;
  background-color: var(--canvas) !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
[data-testid="stSidebarUserContent"] {
  padding-top: 6px !important;
  padding-bottom: 24px !important;
  padding-left: 16px !important;
  padding-right: 16px !important;
  overflow-x: hidden !important;
  box-sizing: border-box !important;
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
  gap: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  width: 100% !important;
}

[data-testid="stSidebar"] .stElementContainer {
  margin: 0 !important;
  padding: 0 !important;
  display: block !important;
  width: 100% !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
  display: block !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] > p {
  margin: 0 !important;
  padding: 0 !important;
}

/* Brand Section: AgriTech Botanical Identity */
.brand-header-card {
  display: flex !important;
  align-items: center !important;
  gap: 11px !important;
  padding: 4px 2px 14px 2px !important;
  margin-bottom: 2px !important;
  border-bottom: 1px solid #e6eee8 !important;
}

.brand-icon-box {
  width: 42px !important;
  height: 42px !important;
  min-width: 42px !important;
  min-height: 42px !important;
  border-radius: 10px !important;
  background-color: #ffffff !important;
  border: 1.5px solid #bbf7d0 !important;
  box-shadow: 0 2px 6px rgba(21, 128, 61, 0.08) !important;
  padding: 2px !important;
  overflow: hidden !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
}

.brand-icon-box img {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain !important;
  display: block !important;
}

.brand-icon-box svg {
  stroke: #15803d !important;
}

.brand-text-col {
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  min-width: 0 !important;
  gap: 2px !important;
}

.brand-title {
  font-size: 15.5px !important;
  font-weight: 700 !important;
  color: #111c16 !important;
  letter-spacing: -0.02em !important;
  line-height: 1.2 !important;
  white-space: nowrap !important;
}

.brand-sub {
  color: #5c6f64 !important;
  font-size: 11.5px !important;
  font-weight: 500 !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1.3 !important;
  display: block !important;
  white-space: nowrap !important;
}

/* Section Headings */
.micro-cap {
  display: block !important;
  font-size: 10.5px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  color: #6b7f73 !important;
  line-height: 14px !important;
  padding-top: 14px !important;
  padding-bottom: 6px !important;
  margin: 0 !important;
  box-sizing: content-box !important;
}

/* Hide native widget label of st.radio ("Menu") */
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stRadio"] > label {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* Sidebar Radio Group — Force 100% Full Width on All Wrappers */
[data-testid="stSidebar"] [data-testid="stRadio"],
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
  overflow: visible !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioGroup"],
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
  display: flex !important;
  flex-direction: column !important;
  align-items: stretch !important;
  width: 100% !important;
  max-width: 100% !important;
  gap: 3px !important;
  margin: 0 !important;
  padding: 2px 0 !important;
  overflow: visible !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div,
[data-testid="stSidebar"] [data-testid="stRadio"] .react-aria-RadioField {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
  display: block !important;
}

/* Sidebar Radio Option — Full-Width SaaS Navigation Item */
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioOption"],
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label {
  display: flex !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  align-items: center !important;
  gap: 11px !important;
  padding: 0 12px !important;
  border-radius: 7px !important;
  min-height: 38px !important;
  height: 38px !important;
  color: #2c3e35 !important;
  font-size: 13.5px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  background-color: transparent !important;
  border: none !important;
  border-left: 3.5px solid transparent !important;
  margin: 0 !important;
  outline: none !important;
  box-shadow: none !important;
  overflow: visible !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label p,
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioOption"] p {
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1.25 !important;
  font-size: 13.5px !important;
  color: inherit !important;
  font-weight: inherit !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label > div {
  display: flex !important;
  align-items: center !important;
  flex: 1 1 auto !important;
  width: 100% !important;
  min-width: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:focus,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:focus-visible,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-focus-visible] {
  outline: none !important;
  box-shadow: none !important;
}

/* Hover inactive item */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover {
  background-color: #f2f7f3 !important;
  color: #111c16 !important;
}

/* Active item: Full-width Pakcoy Green highlight pill with left bar */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked),
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-selected="true"],
[data-testid="stSidebar"] [data-testid="stRadio"] .react-aria-RadioField[data-selected="true"] label {
  background: linear-gradient(90deg, #dcfce7 0%, #f0fdf4 100%) !important;
  color: #14532d !important;
  font-weight: 600 !important;
  border: none !important;
  border-left: 3.5px solid #15803d !important;
  border-radius: 7px !important;
  box-shadow: 0 1px 2px rgba(21, 128, 61, 0.06) !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked):hover,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-selected="true"]:hover {
  background: linear-gradient(90deg, #bbf7d0 0%, #dcfce7 100%) !important;
  color: #14532d !important;
}

/* Hide native circular radio bullet */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label > div > div:first-child {
  display: none !important;
  visibility: hidden !important;
  width: 0 !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* Nav Item SVG Icons via CSS Mask */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label::before {
  content: "" !important;
  display: inline-block !important;
  width: 17px !important;
  height: 17px !important;
  min-width: 17px !important;
  max-width: 17px !important;
  background-color: #5c6f64 !important;
  -webkit-mask-size: contain !important;
  -webkit-mask-repeat: no-repeat !important;
  -webkit-mask-position: center !important;
  mask-size: contain !important;
  mask-repeat: no-repeat !important;
  mask-position: center !important;
  flex-shrink: 0 !important;
  transition: background-color 0.15s ease !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover::before {
  background-color: #111c16 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked)::before,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-selected="true"]::before,
[data-testid="stSidebar"] [data-testid="stRadio"] .react-aria-RadioField[data-selected="true"] label::before {
  background-color: #15803d !important;
}

/* 1. Dashboard (layout-dashboard) */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div:nth-child(1) label::before,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:nth-of-type(1)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E");
}

/* 2. Eksplorasi Data (bar-chart-3) */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div:nth-child(2) label::before,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:nth-of-type(2)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 3v18h18'/%3E%3Cpath d='M18 17V9'/%3E%3Cpath d='M13 17V5'/%3E%3Cpath d='M8 17v-3'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 3v18h18'/%3E%3Cpath d='M18 17V9'/%3E%3Cpath d='M13 17V5'/%3E%3Cpath d='M8 17v-3'/%3E%3C/svg%3E");
}

/* 3. Monitoring Realtime (activity) */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div:nth-child(3) label::before,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:nth-of-type(3)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 12h-4l-3 9L9 3l-3 9H2'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 12h-4l-3 9L9 3l-3 9H2'/%3E%3C/svg%3E");
}

/* 4. Model LSTM (cpu) */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div:nth-child(4) label::before,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:nth-of-type(4)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='16' height='16' x='4' y='4' rx='2'/%3E%3Crect width='6' height='6' x='9' y='9' rx='1'/%3E%3Cpath d='M15 2v2'/%3E%3Cpath d='M15 20v2'/%3E%3Cpath d='M2 15h2'/%3E%3Cpath d='M2 9h2'/%3E%3Cpath d='M20 15h2'/%3E%3Cpath d='M20 9h2'/%3E%3Cpath d='M9 2v2'/%3E%3Cpath d='M9 20v2'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='16' height='16' x='4' y='4' rx='2'/%3E%3Crect width='6' height='6' x='9' y='9' rx='1'/%3E%3Cpath d='M15 2v2'/%3E%3Cpath d='M15 20v2'/%3E%3Cpath d='M2 15h2'/%3E%3Cpath d='M2 9h2'/%3E%3Cpath d='M20 15h2'/%3E%3Cpath d='M20 9h2'/%3E%3Cpath d='M9 2v2'/%3E%3Cpath d='M9 20v2'/%3E%3C/svg%3E");
}

/* 5. Prediksi 4 Hari (calendar-range) */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div:nth-child(5) label::before,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:nth-of-type(5)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='18' height='18' x='3' y='4' rx='2'/%3E%3Cline x1='16' x2='16' y1='2' y2='6'/%3E%3Cline x1='8' x2='8' y1='2' y2='6'/%3E%3Cline x1='3' x2='21' y1='10' y2='10'/%3E%3Cpath d='M17 14h-6'/%3E%3Cpath d='M13 18H7'/%3E%3Cpath d='M7 14h.01'/%3E%3Cpath d='M17 18h.01'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='18' height='18' x='3' y='4' rx='2'/%3E%3Cline x1='16' x2='16' y1='2' y2='6'/%3E%3Cline x1='8' x2='8' y1='2' y2='6'/%3E%3Cline x1='3' x2='21' y1='10' y2='10'/%3E%3Cpath d='M17 14h-6'/%3E%3Cpath d='M13 18H7'/%3E%3Cpath d='M7 14h.01'/%3E%3Cpath d='M17 18h.01'/%3E%3C/svg%3E");
}

/* 6. Model CNN (Scan Foto) (scan-line) */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div:nth-child(6) label::before,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:nth-of-type(6)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 7V5a2 2 0 0 1 2-2h2'/%3E%3Cpath d='M17 3h2a2 2 0 0 1 2 2v2'/%3E%3Cpath d='M21 17v2a2 2 0 0 1-2 2h-2'/%3E%3Cpath d='M7 21H5a2 2 0 0 1-2-2v-2'/%3E%3Cpath d='M7 12h10'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 7V5a2 2 0 0 1 2-2h2'/%3E%3Cpath d='M17 3h2a2 2 0 0 1 2 2v2'/%3E%3Cpath d='M21 17v2a2 2 0 0 1-2 2h-2'/%3E%3Cpath d='M7 21H5a2 2 0 0 1-2-2v-2'/%3E%3Cpath d='M7 12h10'/%3E%3C/svg%3E");
}

/* 7. Scan Gabungan (scan-search) */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div:nth-child(7) label::before,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:nth-of-type(7)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 7V5a2 2 0 0 1 2-2h2'/%3E%3Cpath d='M17 3h2a2 2 0 0 1 2 2v2'/%3E%3Cpath d='M21 17v2a2 2 0 0 1-2 2h-2'/%3E%3Cpath d='M7 21H5a2 2 0 0 1-2-2v-2'/%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3Cpath d='m16 16-1.9-1.9'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 7V5a2 2 0 0 1 2-2h2'/%3E%3Cpath d='M17 3h2a2 2 0 0 1 2 2v2'/%3E%3Cpath d='M21 17v2a2 2 0 0 1-2 2h-2'/%3E%3Cpath d='M7 21H5a2 2 0 0 1-2-2v-2'/%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3Cpath d='m16 16-1.9-1.9'/%3E%3C/svg%3E");
}

/* 8. AI Assistant (message-square) */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div:nth-child(8) label::before,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:nth-of-type(8)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/%3E%3C/svg%3E");
}

/* Sidebar Action Buttons */
.st-key-btn_logout button {
  width: 100% !important;
  height: 36px !important;
  border-radius: 6px !important;
  border: 1px solid #fecaca !important;
  background-color: #fef2f2 !important;
  color: #b91c1c !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  transition: all 0.15s ease !important;
}

.st-key-btn_logout button:hover {
  background-color: #fee2e2 !important;
  border-color: #f87171 !important;
  color: #991b1b !important;
}

/* ================================================================= AI Assistant Framed Card Interface */
.st-key-chat_main_card {
  max-width: 920px !important;
  margin: 0 auto 0 auto !important;
  background-color: #ffffff !important;
  border: 1px solid #dce5de !important;
  border-radius: 12px !important;
  box-shadow: rgba(17, 28, 22, 0.05) 0 4px 16px !important;
  overflow: visible !important;
  box-sizing: border-box !important;
}

.st-key-chat_main_card > div {
  padding: 0 !important;
  gap: 0 !important;
}

/* 1. Header Bingkai */
.st-key-chat_header_row {
  min-height: 62px !important;
  padding: 12px 20px !important;
  border-bottom: 1px solid #dce5de !important;
  background-color: #ffffff !important;
  border-top-left-radius: 11px !important;
  border-top-right-radius: 11px !important;
  display: flex !important;
  align-items: center !important;
}

.chat-header-info {
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
}

.chat-header-icon-box {
  width: 36px !important;
  height: 36px !important;
  min-width: 36px !important;
  min-height: 36px !important;
  border-radius: 8px !important;
  background-color: #f0fdf4 !important;
  border: 1px solid #bbf7d0 !important;
  color: #15803d !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
}

.chat-header-title {
  font-size: 15px !important;
  font-weight: 600 !important;
  color: #111c16 !important;
  line-height: 1.25 !important;
}

.chat-header-sub {
  font-size: 12.5px !important;
  color: #5c6f64 !important;
  line-height: 1.35 !important;
}

/* Trash Icon Button */
.st-key-btn_clear_chat {
  display: flex !important;
  justify-content: flex-end !important;
  align-items: center !important;
}

.st-key-btn_clear_chat button {
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  width: 36px !important;
  height: 36px !important;
  min-height: 36px !important;
  padding: 0 !important;
  border-radius: 8px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer !important;
  position: relative !important;
  color: transparent !important;
}

.st-key-btn_clear_chat button:hover {
  background-color: #fef2f2 !important;
}

.st-key-btn_clear_chat button::after {
  content: "" !important;
  display: block !important;
  width: 18px !important;
  height: 18px !important;
  background-color: #5c6f64 !important;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 6h18'/%3E%3Cpath d='M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6'/%3E%3Cpath d='M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2'/%3E%3Cline x1='10' x2='10' y1='11' y2='17'/%3E%3Cline x1='14' x2='14' y1='11' y2='17'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 6h18'/%3E%3Cpath d='M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6'/%3E%3Cpath d='M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2'/%3E%3Cline x1='10' x2='10' y1='11' y2='17'/%3E%3Cline x1='14' x2='14' y1='11' y2='17'/%3E%3C/svg%3E") !important;
  -webkit-mask-size: contain !important;
  mask-size: contain !important;
  -webkit-mask-repeat: no-repeat !important;
  mask-repeat: no-repeat !important;
  -webkit-mask-position: center !important;
  mask-position: center !important;
  transition: background-color 0.15s ease !important;
}

.st-key-btn_clear_chat button:hover::after {
  background-color: #dc2626 !important;
}

/* 2. Area Pesan */
.st-key-chat_scroll_area {
  background-color: #fafcfa !important;
  border: none !important;
  border-top: none !important;
  border-bottom: none !important;
  padding: 16px 20px !important;
}

/* Keadaan Kosong (Empty State) */
.chat-empty-state {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  text-align: center !important;
  padding: 24px 16px 14px 16px !important;
}

.chat-empty-icon-box {
  width: 44px !important;
  height: 44px !important;
  border-radius: 10px !important;
  background-color: #f0fdf4 !important;
  border: 1px solid #bbf7d0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  margin-bottom: 12px !important;
}

.chat-empty-title {
  font-size: 16px !important;
  font-weight: 600 !important;
  color: #111c16 !important;
  margin-bottom: 4px !important;
}

.chat-empty-sub {
  font-size: 13px !important;
  color: #5c6f64 !important;
  max-width: 460px !important;
  line-height: 1.45 !important;
  margin-bottom: 16px !important;
}

/* 4 Saran Pertanyaan sebagai grid 2x2 kartu kecil */
[class*="st-key-sug_card_"] button,
[class*="st-key-sug_card_"] [data-testid="stBaseButton-secondary"],
.st-key-chat_main_card .st-key-chat_scroll_area [data-testid="stBaseButton-secondary"],
.st-key-chat_main_card .st-key-chat_scroll_area .stButton > button,
.st-key-chat_main_card .st-key-chat_scroll_area .stButton > button[kind="secondary"] {
  background-color: #ffffff !important;
  border: 1px solid #dce5de !important;
  border-radius: 8px !important;
  color: #2c3e35 !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  line-height: 1.45 !important;
  padding: 12px 14px !important;
  text-align: left !important;
  justify-content: flex-start !important;
  align-items: center !important;
  box-shadow: rgba(17, 28, 22, 0.02) 0 1px 2px !important;
  transition: all 0.15s ease !important;
  min-height: 54px !important;
  height: 54px !important;
  white-space: normal !important;
  margin: 0 !important;
  display: flex !important;
  width: 100% !important;
}

[class*="st-key-sug_card_"] button > div,
[class*="st-key-sug_card_"] button > div > span,
[class*="st-key-sug_card_"] button [data-testid="stMarkdownContainer"],
[class*="st-key-sug_card_"] button p,
.st-key-chat_main_card .st-key-chat_scroll_area button > div,
.st-key-chat_main_card .st-key-chat_scroll_area button > div > span,
.st-key-chat_main_card .st-key-chat_scroll_area button [data-testid="stMarkdownContainer"],
.st-key-chat_main_card .st-key-chat_scroll_area button p {
  text-align: left !important;
  width: 100% !important;
  justify-content: flex-start !important;
  align-items: center !important;
  display: flex !important;
}

[class*="st-key-sug_card_"] button:hover,
[class*="st-key-sug_card_"] [data-testid="stBaseButton-secondary"]:hover,
.st-key-chat_main_card .st-key-chat_scroll_area [data-testid="stBaseButton-secondary"]:hover,
.st-key-chat_main_card .st-key-chat_scroll_area .stButton > button:hover,
.st-key-chat_main_card .st-key-chat_scroll_area .stButton > button[kind="secondary"]:hover {
  background-color: #f0fdf4 !important;
  border-color: #15803d !important;
  color: #14532d !important;
  box-shadow: rgba(21, 128, 61, 0.08) 0 2px 6px !important;
}

/* Base Message Row in Scroll Area */
[data-testid="stChatMessage"] {
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 0 12px 0 !important;
  width: 100% !important;
  display: flex !important;
  align-items: flex-start !important;
}

[data-testid="stChatMessage"]:last-child {
  margin-bottom: 4px !important;
}

/* ================================================================= User Message */
[data-testid="stChatMessage"][aria-label*="user" i],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
[data-testid="stChatMessage"]:has([data-testid*="User"]),
[data-testid="stChatMessage"]:has([aria-label*="user" i]) {
  flex-direction: row-reverse !important;
  justify-content: flex-start !important;
}

[data-testid="stChatMessage"][aria-label*="user" i] [data-testid*="Avatar"],
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessage"] [data-testid*="AvatarUser"],
[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid*="Avatar"] {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* User Bubble: Hijau Pakcoy #15803d */
[data-testid="stChatMessage"][aria-label*="user" i] [data-testid="stChatMessageContent"],
[data-testid="stChatMessageContent"][aria-label*="user" i],
[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stChatMessageContent"] {
  background-color: #15803d !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 14px 14px 4px 14px !important;
  padding: 12px 16px !important;
  box-shadow: rgba(21, 128, 61, 0.14) 0 2px 6px !important;
  max-width: 75% !important;
  width: fit-content !important;
  margin-left: auto !important;
  margin-right: 0 !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  flex-grow: 0 !important;
  overflow: visible !important;
  height: auto !important;
  min-height: auto !important;
}

[data-testid="stChatMessage"][aria-label*="user" i] [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"][aria-label*="user" i] [data-testid="stChatMessageContent"] p,
[data-testid="stChatMessage"][aria-label*="user" i] [data-testid="stChatMessageContent"] span,
[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stChatMessageContent"] p,
[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stChatMessageContent"] span {
  color: #ffffff !important;
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
  font-size: 14px !important;
  line-height: 1.5 !important;
  margin: 0 !important;
  padding: 0 !important;
  white-space: pre-wrap !important;
  word-break: break-word !important;
  overflow: visible !important;
  height: auto !important;
}

/* ================================================================= Assistant Message */
[data-testid="stChatMessage"][aria-label*="assistant" i],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]),
[data-testid="stChatMessage"]:has([data-testid*="Assistant"]),
[data-testid="stChatMessage"]:has([aria-label*="assistant" i]),
[data-testid="stChatMessage"]:not([aria-label*="user" i]):not(:has([data-testid*="User"])) {
  flex-direction: row !important;
  justify-content: flex-start !important;
  gap: 10px !important;
}

/* Assistant Avatar: Kotak 28px #f0fdf4 dengan ikon sprout hijau #15803d */
[data-testid="stChatMessageAvatarAssistant"],
[data-testid="stChatMessage"] [data-testid*="AvatarAssistant"],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid*="Avatar"],
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid*="Avatar"] {
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  width: 28px !important;
  height: 28px !important;
  min-width: 28px !important;
  min-height: 28px !important;
  max-width: 28px !important;
  max-height: 28px !important;
  border-radius: 6px !important;
  background-color: #f0fdf4 !important;
  border: 1px solid #bbf7d0 !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
  margin-top: 2px !important;
  font-size: 0 !important;
  position: relative !important;
  overflow: hidden !important;
}

[data-testid="stChatMessageAvatarAssistant"] *,
[data-testid="stChatMessage"] [data-testid*="AvatarAssistant"] *,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid*="Avatar"] * {
  display: none !important;
}

[data-testid="stChatMessageAvatarAssistant"]::after,
[data-testid="stChatMessage"] [data-testid*="AvatarAssistant"]::after,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid*="Avatar"]::after {
  content: "" !important;
  display: block !important;
  width: 16px !important;
  height: 16px !important;
  background-color: #15803d !important;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7 20h10'/%3E%3Cpath d='M10 20c5.5-2.5.8-6.4 3-10'/%3E%3Cpath d='M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4.1 5.5.8z'/%3E%3Cpath d='M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7 20h10'/%3E%3Cpath d='M10 20c5.5-2.5.8-6.4 3-10'/%3E%3Cpath d='M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4.1 5.5.8z'/%3E%3Cpath d='M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z'/%3E%3C/svg%3E") !important;
  -webkit-mask-size: contain !important;
  mask-size: contain !important;
  -webkit-mask-repeat: no-repeat !important;
  mask-repeat: no-repeat !important;
  -webkit-mask-position: center !important;
  mask-position: center !important;
}

/* Assistant Bubble */
[data-testid="stChatMessageContent"][aria-label*="assistant"],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"],
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] {
  background-color: #ffffff !important;
  color: #111c16 !important;
  border: 1px solid #dce5de !important;
  border-radius: 14px 14px 14px 4px !important;
  padding: 12px 16px !important;
  box-shadow: rgba(17, 28, 22, 0.03) 0 1px 3px !important;
  max-width: 85% !important;
  width: fit-content !important;
  margin-left: 0 !important;
  margin-right: auto !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  overflow: visible !important;
  height: auto !important;
  min-height: auto !important;
  flex-grow: 0 !important;
}

[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] p,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] li,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] ul,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] ol,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] strong,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] em,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] span {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  color: #111c16 !important;
}

[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] li p {
  margin: 0 !important;
  padding: 0 !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  color: #111c16 !important;
}

[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] ul,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] ol {
  margin-top: 6px !important;
  margin-bottom: 6px !important;
  padding-left: 20px !important;
}

[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] li {
  margin-bottom: 6px !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  color: #111c16 !important;
}

[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] li:last-child {
  margin-bottom: 0 !important;
}

[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] ul ul,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] ol ul {
  list-style-type: circle !important;
  margin-top: 4px !important;
  margin-bottom: 4px !important;
  padding-left: 18px !important;
}

[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] h1,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] h2,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] h3,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] h4 {
  font-size: 15px !important;
  font-weight: 600 !important;
  color: #111c16 !important;
  margin-top: 8px !important;
  margin-bottom: 6px !important;
  line-height: 1.4 !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] pre,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
  background-color: #f6f8f6 !important;
  border: 1px solid #dce5de !important;
  border-radius: 6px !important;
  font-size: 13px !important;
}

/* Typing Indicator Animation */
.typing-indicator {
  display: inline-flex !important;
  align-items: center !important;
  gap: 5px !important;
  padding: 6px 10px !important;
}

.typing-dot {
  width: 6px !important;
  height: 6px !important;
  background-color: #15803d !important;
  border-radius: 50% !important;
  display: inline-block !important;
  animation: typingBounce 1.4s infinite ease-in-out both !important;
}

.typing-dot:nth-child(1) { animation-delay: -0.32s !important; }
.typing-dot:nth-child(2) { animation-delay: -0.16s !important; }
.typing-dot:nth-child(3) { animation-delay: 0s !important; }

@keyframes typingBounce {
  0%, 80%, 100% {
    transform: scale(0.3);
    opacity: 0.3;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Small In-flow Error Notice */
.chat-error-notice {
  background-color: #fef2f2 !important;
  border-left: 3px solid #dc2626 !important;
  color: #111c16 !important;
  font-size: 13px !important;
  padding: 10px 14px !important;
  border-radius: 0 8px 8px 0 !important;
  margin: 8px 0 !important;
  line-height: 1.45 !important;
}

/* 3. Area Input */
.st-key-chat_input_section {
  border-top: 1px solid #dce5de !important;
  padding: 14px 20px 16px 20px !important;
  background-color: #ffffff !important;
  border-bottom-left-radius: 11px !important;
  border-bottom-right-radius: 11px !important;
  display: flex !important;
  flex-direction: column !important;
  box-sizing: border-box !important;
}

.st-key-chat_input_section [data-testid="stVerticalBlock"] {
  gap: 10px !important;
}

.st-key-chat_input_section .stElementContainer {
  margin: 0 !important;
  padding: 0 !important;
}

.st-key-chat_input_section [data-testid="stMarkdownContainer"] {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  padding: 0 !important;
  margin: 0 !important;
}

.st-key-chat_input_section [data-testid="stMarkdownContainer"] > p {
  margin: 0 !important;
  padding: 0 !important;
  display: flex !important;
  justify-content: center !important;
}

.st-key-chat_input_section [data-testid="stChatInput"] {
  position: static !important;
  width: 100% !important;
  max-width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

.st-key-chat_input_section [data-testid="stChatInput"] > div {
  border-radius: 8px !important;
  border: 1px solid #b8c9be !important;
  background-color: #ffffff !important;
  box-shadow: none !important;
  outline: none !important;
  padding: 4px 6px 4px 12px !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
  display: flex !important;
  align-items: center !important;
}

.st-key-chat_input_section [data-testid="stChatInput"] > div:focus-within {
  border-color: #15803d !important;
  box-shadow: 0 0 0 3px rgba(21, 128, 61, 0.12) !important;
  outline: none !important;
}

.st-key-chat_input_section [data-testid="stChatInput"] textarea,
.st-key-chat_input_section [data-testid="stChatInputTextArea"] {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
  font-size: 14px !important;
  color: #111c16 !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  background: transparent !important;
  padding: 4px 0 !important;
}

.st-key-chat_input_section [data-testid="stChatInput"] textarea:focus,
.st-key-chat_input_section [data-testid="stChatInputTextArea"]:focus {
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}

.st-key-chat_input_section [data-testid="stChatInput"] div:has(> [data-testid="stChatInputSubmitButton"]),
.st-key-chat_input_section [data-testid="stChatInput"] div.st-emotion-cache-k1jj38 {
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  background: transparent !important;
  padding: 0 !important;
  margin: 0 !important;
}

[data-testid="stChatInputSubmitButton"],
.st-key-chat_input_section [data-testid="stChatInputSubmitButton"],
.st-key-chat_input_section button[aria-label="Send message"],
.st-key-chat_input_section [data-testid="stChatInput"] button {
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  border-radius: 6px !important;
  width: 32px !important;
  height: 32px !important;
  min-width: 32px !important;
  min-height: 32px !important;
  max-width: 32px !important;
  max-height: 32px !important;
  padding: 0 !important;
  margin: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  background-color: #15803d !important;
  color: #ffffff !important;
  transition: all 0.15s ease !important;
  cursor: pointer !important;
}

[data-testid="stChatInputSubmitButton"] svg,
.st-key-chat_input_section [data-testid="stChatInputSubmitButton"] svg,
.st-key-chat_input_section [data-testid="stChatInput"] button svg {
  fill: currentColor !important;
  stroke: currentColor !important;
  color: inherit !important;
  width: 18px !important;
  height: 18px !important;
  border: none !important;
  outline: none !important;
}

.st-key-chat_input_section [data-testid="stChatInputSubmitButton"]:hover:not(:disabled),
.st-key-chat_input_section [data-testid="stChatInput"] button:hover:not(:disabled) {
  background-color: #166534 !important;
  color: #ffffff !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}

.st-key-chat_input_section [data-testid="stChatInputSubmitButton"]:disabled,
.st-key-chat_input_section [data-testid="stChatInput"] button:disabled {
  background: transparent !important;
  background-color: transparent !important;
  color: #b8c9be !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  cursor: default !important;
}

.st-key-chat_input_section [data-testid="stChatInputSubmitButton"]:disabled svg,
.st-key-chat_input_section [data-testid="stChatInput"] button:disabled svg {
  fill: #b8c9be !important;
  stroke: #b8c9be !important;
  color: #b8c9be !important;
  border: none !important;
  outline: none !important;
}

.st-key-chat_input_section [data-testid="stChatInputSubmitButton"]:focus,
.st-key-chat_input_section [data-testid="stChatInputSubmitButton"]:focus-visible,
.st-key-chat_input_section [data-testid="stChatInput"] button:focus,
.st-key-chat_input_section [data-testid="stChatInput"] button:focus-visible {
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}

.chat-frame-footer-note {
  font-size: 11px !important;
  color: #5c6f64 !important;
  text-align: center !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1.4 !important;
  display: block !important;
  width: 100% !important;
}

@media (max-width: 768px) {
  .st-key-chat_main_card {
    margin: 0 12px 16px 12px !important;
    max-width: calc(100% - 24px) !important;
  }
  .st-key-chat_scroll_area {
    padding: 14px 12px !important;
  }
}

/* Sidebar Uploader (DATA & SISTEM) — Compact & Clean */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
  margin: 0 !important;
  padding: 0 !important;
  display: block !important;
  width: 100% !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] > label,
[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stFileUploader"] label p {
  font-size: 12px !important;
  font-weight: 500 !important;
  color: #5c6f64 !important;
  margin: 0 0 4px 0 !important;
  padding: 0 !important;
  line-height: 1.3 !important;
  display: block !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] section,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
  padding: 6px 8px !important;
  background-color: #f8faf8 !important;
  border: 1px dashed #c5d3ca !important;
  border-radius: 8px !important;
  min-height: auto !important;
  margin: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.15s ease !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] section:hover,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
  border-color: #15803d !important;
  background-color: #f0fdf4 !important;
}

/* Hide noisy "200MB per file • XLSX" instruction text in sidebar dropzone */
[data-testid="stSidebar"] [data-testid="stFileUploader"] section small,
[data-testid="stSidebar"] [data-testid="stFileUploaderInstructions"],
[data-testid="stSidebar"] [data-testid="stFileUploaderInstructions"] small,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] > div:first-child {
  display: none !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
  width: 100% !important;
  height: 32px !important;
  min-height: 32px !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  background-color: #ffffff !important;
  color: #166534 !important;
  border: 1px solid #c5d3ca !important;
  border-radius: 6px !important;
  padding: 0 12px !important;
  box-shadow: none !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  transition: all 0.15s ease !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button:hover {
  background-color: #f0fdf4 !important;
  border-color: #15803d !important;
  color: #14532d !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button [data-testid="stIconMaterial"],
[data-testid="stSidebar"] [data-testid="stFileUploader"] button span[class*="material"] {
  color: #15803d !important;
  font-size: 16px !important;
  margin-right: 2px !important;
}

/* Sidebar Buttons */
[data-testid="stSidebar"] .stButton {
  margin: 7px 0 0 0 !important;
  padding: 0 !important;
  width: 100% !important;
  display: block !important;
}

[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] .stButton > button[kind="secondary"],
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .st-key-reload_models button,
.st-key-reload_models button {
  width: 100% !important;
  height: 34px !important;
  min-height: 34px !important;
  max-height: 34px !important;
  border-radius: 7px !important;
  background-color: #ffffff !important;
  color: #2c3e35 !important;
  border: 1px solid #d5e0d8 !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  padding: 0 14px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: none !important;
  transition: all 0.15s ease !important;
}

[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
[data-testid="stSidebar"] .st-key-reload_models button:hover,
.st-key-reload_models button:hover {
  background-color: #f0fdf4 !important;
  border-color: #86efac !important;
  color: #14532d !important;
}

/* Sidebar Logout Button ("Keluar Akun") — Specific Override */
[data-testid="stSidebar"] .st-key-btn_logout button,
.st-key-btn_logout button {
  width: 100% !important;
  height: 34px !important;
  min-height: 34px !important;
  max-height: 34px !important;
  border-radius: 7px !important;
  border: 1px solid #fecdd3 !important;
  background-color: #fff1f2 !important;
  color: #be123c !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  transition: all 0.15s ease !important;
}

[data-testid="stSidebar"] .st-key-btn_logout button:hover,
.st-key-btn_logout button:hover {
  background-color: #ffe4e6 !important;
  border-color: #fda4af !important;
  color: #9f1239 !important;
}

[data-testid="stSidebar"] .st-key-btn_logout button::before {
  content: "" !important;
  display: inline-block !important;
  width: 14px !important;
  height: 14px !important;
  min-width: 14px !important;
  margin-right: 7px !important;
  background-color: currentColor !important;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4'/%3E%3Cpolyline points='16 17 21 12 16 7'/%3E%3Cline x1='21' x2='9' y1='12' y2='12'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4'/%3E%3Cpolyline points='16 17 21 12 16 7'/%3E%3Cline x1='21' x2='9' y1='12' y2='12'/%3E%3C/svg%3E") !important;
  -webkit-mask-size: contain !important;
  mask-size: contain !important;
  -webkit-mask-repeat: no-repeat !important;
  mask-repeat: no-repeat !important;
}

/* Sidebar Divider */
[data-testid="stSidebar"] hr,
[data-testid="stSidebar"] [data-testid="stDivider"] {
  border: none !important;
  border-top: 1px solid #edf2ee !important;
  height: 1px !important;
  margin-top: 20px !important;
  margin-bottom: 12px !important;
  padding: 0 !important;
  display: block !important;
  clear: both !important;
}

/* Sidebar Footer Caption */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] .stCaption {
  margin-top: 10px !important;
  padding: 0 !important;
  display: block !important;
  clear: both !important;
  text-align: center !important;
}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] .stCaption p {
  font-size: 11px !important;
  color: #6b7f73 !important;
  line-height: 1.4 !important;
  margin: 0 !important;
  padding: 0 !important;
  text-align: center !important;
}

/* Button SVG icons */
.st-key-reload_models button::before {
  content: "" !important;
  display: inline-block !important;
  width: 14px !important;
  height: 14px !important;
  margin-right: 7px !important;
  background-color: #5c6f64 !important;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8'/%3E%3Cpath d='M21 3v5h-5'/%3E%3Cpath d='M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16'/%3E%3Cpath d='M3 21v-5h5'/%3E%3C/svg%3E") no-repeat center / contain !important;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8'/%3E%3Cpath d='M21 3v5h-5'/%3E%3Cpath d='M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16'/%3E%3Cpath d='M3 21v-5h5'/%3E%3C/svg%3E") no-repeat center / contain !important;
  flex-shrink: 0 !important;
  transition: background-color 0.15s ease !important;
}

.st-key-reload_models button:hover::before {
  background-color: #15803d !important;
}

.st-key-mon_run button::before {
  content: "" !important;
  display: inline-block !important;
  width: 15px !important;
  height: 15px !important;
  margin-right: 6px !important;
  background-color: currentColor !important;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolygon points='6 3 20 12 6 21 6 3'/%3E%3C/svg%3E") no-repeat center / contain !important;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolygon points='6 3 20 12 6 21 6 3'/%3E%3C/svg%3E") no-repeat center / contain !important;
}

.st-key-eks_dl button::before,
.st-key-fc_dl button::before,
.st-key-scan_dl button::before {
  content: "" !important;
  display: inline-block !important;
  width: 15px !important;
  height: 15px !important;
  margin-right: 6px !important;
  background-color: currentColor !important;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='7 10 12 15 17 10'/%3E%3Cline x1='12' x2='12' y1='15' y2='3'/%3E%3C/svg%3E") no-repeat center / contain !important;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='7 10 12 15 17 10'/%3E%3Cline x1='12' x2='12' y1='15' y2='3'/%3E%3C/svg%3E") no-repeat center / contain !important;
}

/* ================================================================= Page Header (Enterprise SaaS Top Bar) */
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: #ffffff;
  border: 1px solid #dce5de;
  border-radius: 10px;
  padding: 16px 22px;
  margin-bottom: 14px;
  box-shadow: 0 1px 2px rgba(17, 28, 22, 0.03);
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.hero-icon-box {
  width: 42px;
  height: 42px;
  min-width: 42px;
  border-radius: 9px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hero-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.hero-title {
  margin: 0 !important;
  padding: 0 !important;
  font-size: 18px !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em !important;
  line-height: 1.25 !important;
  color: #111c16 !important;
}

.hero-sub {
  margin: 0 !important;
  padding: 0 !important;
  color: #5c6f64 !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  line-height: 1.4 !important;
}

.hero-right {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.hero-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  border-radius: 999px;
  background: #f8faf8;
  border: 1px solid #dce5de;
  font-size: 11.5px;
  font-weight: 600;
  color: #2c3e35;
  white-space: nowrap;
}

.hero-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #16a34a;
}

@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }
  .hero-right {
    display: none;
  }
}

/* ================================================================= Telemetry KPI Cards (Clean Enterprise Grid) */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin: 8px 0 12px;
}

.kpi-grid.cols-5 {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.kpi-grid.cols-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.kpi-grid.cols-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.kpi-grid.cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 1100px) {
  .kpi-grid.cols-5, .kpi-grid.cols-4 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.kpi {
  background: #ffffff;
  border: 1px solid #dce5de;
  border-radius: 10px;
  padding: 15px 18px;
  box-shadow: 0 1px 2px rgba(17, 28, 22, 0.03);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  min-height: 104px;
  box-sizing: border-box;
}

.kpi:hover {
  border-color: #86efac;
  box-shadow: 0 4px 12px rgba(21, 128, 61, 0.06);
}

.kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  min-height: 28px;
}

.kpi-label {
  color: #5c6f64;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kpi-icon-pill {
  width: 28px;
  height: 28px;
  min-width: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-value {
  font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
  letter-spacing: -0.025em;
  color: #111c16;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kpi-sub {
  color: #6b7f73;
  font-size: 11.5px;
  font-weight: 400;
  margin-top: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ================================================================= Maturity Legend Bar & Filter Info Bar */
.legend-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  background: #ffffff;
  border: 1px solid #dce5de;
  border-radius: 8px;
  padding: 9px 16px;
  margin: 0 0 18px 0;
  font-size: 12px;
  color: #2c3e35;
}

.legend-strip-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #111c16;
}

.legend-pills {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.legend-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 500;
  background: #f8faf8;
  border: 1px solid #e2ebe4;
  color: #2c3e35;
}

.legend-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}

.filter-summary-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 8px;
  margin-top: 4px;
  border-top: 1px solid #edf2ee;
  font-size: 12px;
  color: #5c6f64;
}

/* ================================================================= Section Header Bar */
.sec-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 18px 0 10px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #dce5de;
}

.sec-header-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sec-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15.5px;
  font-weight: 700;
  color: #111c16;
  letter-spacing: -0.015em;
}

.sec-header-sub {
  font-size: 12.5px;
  color: #5c6f64;
}

/* ================================================================= Live Telemetry Console */
.live-console-card {
  background: #ffffff;
  border: 1px solid #dce5de;
  border-radius: 10px;
  padding: 16px 20px;
  margin: 8px 0 14px 0;
  box-shadow: 0 1px 3px rgba(17, 28, 22, 0.03);
}

.live-console-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  padding-bottom: 12px;
  margin-bottom: 14px;
  border-bottom: 1px solid #edf2ee;
}

.live-console-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.live-meta-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 11px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  background: #f0fdf4;
  color: #14532d;
  border: 1px solid #bbf7d0;
}

.live-meta-step {
  font-size: 12px;
  font-weight: 500;
  color: #5c6f64;
}

.live-prog-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 220px;
}

.live-prog-track {
  flex: 1;
  height: 7px;
  background: #edf2ee;
  border-radius: 999px;
  overflow: hidden;
}

.live-prog-fill {
  height: 100%;
  background: #15803d;
  border-radius: 999px;
  transition: width 0.25s ease;
}

.live-prog-pct {
  font-size: 11.5px;
  font-weight: 700;
  color: #15803d;
  font-variant-numeric: tabular-nums;
}

.live-metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

@media (max-width: 1024px) {
  .live-metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.live-metric-box {
  background: #f8faf8;
  border: 1px solid #e2ebe4;
  border-radius: 8px;
  padding: 12px 15px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.live-metric-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 6px;
}

.live-metric-lbl {
  font-size: 11px;
  font-weight: 600;
  color: #5c6f64;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.live-metric-badge {
  font-size: 10.5px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
}

.live-metric-val {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
  font-size: 20px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #111c16;
  line-height: 1.25;
  letter-spacing: -0.02em;
}

.live-metric-sub {
  font-size: 11.5px;
  color: #6b7f73;
  margin-top: 4px;
}

/* ================================================================= Status Banners */
.banner {
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin: 10px 0;
  border: 1px solid var(--hairline);
  border-left: 4px solid;
  font-size: 13.5px;
  line-height: 1.45;
  font-weight: 500;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.banner-icon {
  flex-shrink: 0;
  margin-top: 1px;
  display: inline-flex;
}

.banner-text {
  flex-grow: 1;
}

.banner.ok {
  background: #f0fdf4;
  border-color: #bbf7d0;
  border-left-color: #15803d;
  color: #14532d;
}

.banner.ok .banner-icon { color: #15803d; }

.banner.warn {
  background: #fffbeb;
  border-color: #fde68a;
  border-left-color: #d97706;
  color: #78350f;
}

.banner.warn .banner-icon { color: #d97706; }

.banner.danger {
  background: #fef2f2;
  border-color: #fecaca;
  border-left-color: #dc2626;
  color: #7f1d1d;
}

.banner.danger .banner-icon { color: #dc2626; }

.banner.info {
  background: #f0fdf4;
  border-color: #bbf7d0;
  border-left-color: #166534;
  color: #111c16;
}

.banner.info .banner-icon { color: #15803d; }

/* ================================================================= LIVE Telemetry Badge */
.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #86efac;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.live-badge.paused {
  background: #f1f5f2;
  color: var(--ink-mute);
  border-color: var(--hairline);
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #16a34a;
  animation: pulseGreen 1.6s infinite;
}

.paused .live-dot {
  background: var(--ink-mute);
  animation: none;
}

@keyframes pulseGreen {
  0% { box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.55); }
  70% { box-shadow: 0 0 0 7px rgba(22, 163, 74, 0); }
  100% { box-shadow: 0 0 0 0 rgba(22, 163, 74, 0); }
}

/* ================================================================= Section Title & Chart Cards */
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
  margin: 14px 0 8px 0;
  letter-spacing: -0.01em;
}

.section-icon {
  display: inline-flex;
  align-items: center;
  color: #15803d;
}

/* Wrap Plotly charts inside clean white structural panels */
[data-testid="stPlotlyChart"] {
  background: #ffffff !important;
  border: 1px solid var(--hairline) !important;
  border-radius: var(--radius-lg) !important;
  padding: 8px 10px 4px 10px !important;
  box-shadow: 0 1px 2px rgba(17, 28, 22, 0.03) !important;
}

/* Override legacy inline indigo badge styles in app.py */
div[style*="#eef2ff"] {
  background: #f0fdf4 !important;
  color: #14532d !important;
  border-color: #bbf7d0 !important;
  border-radius: 6px !important;
}

/* Streamlit Native Components Overrides — Proportional SaaS Button System */
.stButton > button[kind="primary"] {
  background-color: #15803d !important;
  color: #ffffff !important;
  border-radius: 8px !important;
  border: 1px solid #166534 !important;
  font-weight: 600 !important;
  height: 38px !important;
  min-height: 38px !important;
  max-height: 38px !important;
  padding: 0 18px !important;
  box-shadow: 0 1px 2px rgba(20, 83, 45, 0.14) !important;
  font-size: 13px !important;
  letter-spacing: 0.01em !important;
  white-space: nowrap !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.15s ease !important;
}

.stButton > button[kind="primary"]:hover {
  background-color: #166534 !important;
  border-color: #14532d !important;
  color: #ffffff !important;
  box-shadow: 0 2px 6px rgba(20, 83, 45, 0.22) !important;
}

.main .stButton > button[kind="secondary"]:not([class*="btn_toggle_mode"]),
[data-testid="stMainBlockContainer"] div:not([class*="sug_card_"]):not(.st-key-chat_header_row):not(.st-key-btn_toggle_mode) > .stButton > button[kind="secondary"] {
  background-color: #ffffff !important;
  color: #166534 !important;
  border: 1px solid #c2d4c8 !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  height: 38px !important;
  min-height: 38px !important;
  max-height: 38px !important;
  padding: 0 15px !important;
  font-size: 13px !important;
  white-space: nowrap !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.15s ease !important;
}

.main .stButton > button[kind="secondary"]:hover,
[data-testid="stMainBlockContainer"] div:not([class*="sug_card_"]):not(.st-key-chat_header_row):not(.st-key-btn_toggle_mode) > .stButton > button[kind="secondary"]:hover {
  background-color: #f0fdf4 !important;
  border-color: #15803d !important;
  color: #14532d !important;
}

/* Action Bar Primary Buttons: Compact Width & Right-Aligned */
.st-key-btn_cls_run .stButton,
.st-key-btn_fc_run .stButton,
.st-key-btn_cnn_run .stButton,
.st-key-btn_scan_run .stButton {
  display: flex !important;
  justify-content: flex-end !important;
  width: 100% !important;
}

.st-key-btn_cls_run button,
.st-key-btn_fc_run button,
.st-key-btn_cnn_run button,
.st-key-btn_scan_run button {
  width: auto !important;
  min-width: 175px !important;
  max-width: 235px !important;
  height: 38px !important;
  min-height: 38px !important;
  max-height: 38px !important;
  padding: 0 18px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
}

div[class*="apply_btn"] button {
  width: 100% !important;
  height: 38px !important;
  min-height: 38px !important;
  max-height: 38px !important;
  padding: 0 16px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
}

/* Quick-Preset Chip Buttons (Hari ke-7, Hari ke-17, Hari ke-25, Template Sensor) */
div[class*="mon_btn"] button,
div[class*="btn_cls_p"] button,
div[class*="btn_tmpl_"] button,
div[class*="fc_btn"] button,
div[class*="scan_btn"] button {
  height: 38px !important;
  min-height: 38px !important;
  max-height: 38px !important;
  padding: 0 12px !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  background-color: #f6faf7 !important;
  border: 1px solid #c9d9ce !important;
  color: #1f3328 !important;
}

div[class*="mon_btn"] button:hover,
div[class*="btn_cls_p"] button:hover,
div[class*="btn_tmpl_"] button:hover,
div[class*="fc_btn"] button:hover,
div[class*="scan_btn"] button:hover {
  background-color: #dcfce7 !important;
  border-color: #15803d !important;
  color: #14532d !important;
}

.stDownloadButton > button {
  background-color: #ffffff !important;
  color: #166534 !important;
  border: 1px solid #c2d4c8 !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
  padding: 0 16px !important;
  font-size: 12.5px !important;
  width: auto !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.15s ease !important;
}

.stDownloadButton > button:hover {
  background-color: #f0fdf4 !important;
  border-color: #15803d !important;
  color: #14532d !important;
}

/* ================================================================= Form Controls & Inputs (Streamlit 1.66+ React-Aria & BaseWeb) */
[data-testid="stWidgetLabel"] p {
  font-size: 12.5px !important;
  font-weight: 600 !important;
  color: #26382f !important;
}

[data-testid="stSelectbox"] .react-aria-Group,
[data-testid="stSelectbox"] [class*="e1oobldh0"],
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] .react-aria-Group,
[data-testid="stMultiSelect"] [class*="ew56mvo0"],
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
[data-testid="stNumberInput"] [data-testid="stNumberInputContainer"],
[data-testid="stNumberInput"] [class*="e1gm8nhx0"],
[data-testid="stTextInput"] [data-testid="stTextInputRootElement"],
[data-testid="stTextInput"] [class*="e1bh1cux2"] {
  background-color: #ffffff !important;
  border: 1px solid #b8c9be !important;
  border-top: 1px solid #b8c9be !important;
  border-right: 1px solid #b8c9be !important;
  border-bottom: 1px solid #b8c9be !important;
  border-left: 1px solid #b8c9be !important;
  border-radius: 8px !important;
  color: #111c16 !important;
  min-height: 38px !important;
  box-shadow: 0 1px 2px rgba(17, 28, 22, 0.03) !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease !important;
}

[data-testid="stSelectbox"] .react-aria-Group:hover,
[data-testid="stSelectbox"] [class*="e1oobldh0"]:hover,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
[data-testid="stMultiSelect"] .react-aria-Group:hover,
[data-testid="stMultiSelect"] [class*="ew56mvo0"]:hover,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:hover,
[data-testid="stNumberInput"] [data-testid="stNumberInputContainer"]:hover,
[data-testid="stNumberInput"] [class*="e1gm8nhx0"]:hover,
[data-testid="stTextInput"] [data-testid="stTextInputRootElement"]:hover,
[data-testid="stTextInput"] [class*="e1bh1cux2"]:hover {
  border-color: #15803d !important;
  border-top-color: #15803d !important;
  border-right-color: #15803d !important;
  border-bottom-color: #15803d !important;
  border-left-color: #15803d !important;
  background-color: #f8fbf9 !important;
}

[data-testid="stSelectbox"] .react-aria-Group[data-focus-within],
[data-testid="stSelectbox"] [class*="e1oobldh0"][data-focus-within],
[data-testid="stSelectbox"] .react-aria-Group:focus-within,
[data-testid="stSelectbox"] [class*="e1oobldh0"]:focus-within,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
[data-testid="stMultiSelect"] .react-aria-Group[data-focus-within],
[data-testid="stMultiSelect"] [class*="ew56mvo0"][data-focus-within],
[data-testid="stMultiSelect"] .react-aria-Group:focus-within,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:focus-within,
[data-testid="stNumberInput"] [data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stNumberInput"] [class*="e1gm8nhx0"]:focus-within,
[data-testid="stTextInput"] [data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stTextInput"] [class*="e1bh1cux2"]:focus-within {
  border-color: #15803d !important;
  border-top-color: #15803d !important;
  border-right-color: #15803d !important;
  border-bottom-color: #15803d !important;
  border-left-color: #15803d !important;
  background-color: #ffffff !important;
  box-shadow: 0 0 0 3px rgba(21, 128, 61, 0.14) !important;
}

[data-testid="stSelectbox"] input,
[data-testid="stSelectbox"] .react-aria-Input,
[data-testid="stMultiSelect"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
  color: #111c16 !important;
  font-weight: 500 !important;
  font-size: 13.5px !important;
  background-color: transparent !important;
}

[data-testid="stSelectbox"] button,
[data-testid="stMultiSelect"] button {
  color: #4b6154 !important;
}

/* Main Area File Uploader Dropzone (Cek Foto & Diagnosis Lengkap) */
[data-testid="stMainBlockContainer"] [data-testid="stFileUploader"] section,
[data-testid="stMainBlockContainer"] [data-testid="stFileUploaderDropzone"] {
  background-color: #f8fbf9 !important;
  border: 1.5px dashed #86efac !important;
  border-radius: 10px !important;
  padding: 14px 18px !important;
  transition: all 0.15s ease !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stFileUploader"] section:hover,
[data-testid="stMainBlockContainer"] [data-testid="stFileUploaderDropzone"]:hover {
  background-color: #f0fdf4 !important;
  border-color: #15803d !important;
}

/* Upload Button in Dropzone */
[data-testid="stMainBlockContainer"] [data-testid="stFileUploader"] section button,
[data-testid="stMainBlockContainer"] [data-testid="stFileUploaderDropzone"] button {
  background-color: #ffffff !important;
  border: 1.5px solid #15803d !important;
  color: #15803d !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  border-radius: 8px !important;
  padding: 5px 16px !important;
  box-shadow: 0 1px 2px rgba(21, 128, 61, 0.08) !important;
  transition: all 0.15s ease !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stFileUploader"] section button:hover,
[data-testid="stMainBlockContainer"] [data-testid="stFileUploaderDropzone"] button:hover {
  background-color: #15803d !important;
  color: #ffffff !important;
  box-shadow: 0 2px 4px rgba(21, 128, 61, 0.18) !important;
}

/* Pastikan Tombol Help Tooltip (?) Streamlit Tidak Kena Border Hijau */
[data-testid="stTooltipHoverTarget"] button,
[data-testid="stWidgetLabel"] button,
[data-testid="stFileUploader"] [data-testid="stWidgetLabel"] button {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  border-radius: 50% !important;
  width: auto !important;
  height: auto !important;
  min-height: auto !important;
}

/* Kustomisasi Teks Batas Upload Menjadi Bahasa Indonesia & Badge Rapi */
[data-testid="stMainBlockContainer"] [data-testid="stFileUploaderInstructions"],
[data-testid="stMainBlockContainer"] [data-testid="stFileUploader"] section small {
  font-size: 0 !important;
  display: inline-flex !important;
  align-items: center !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stFileUploaderInstructions"]::after,
[data-testid="stMainBlockContainer"] [data-testid="stFileUploader"] section small::after {
  content: "Maksimal 10 MB per foto • Format JPG, JPEG, PNG" !important;
  font-size: 12.5px !important;
  font-weight: 500 !important;
  color: #2e4438 !important;
  background: #edf7ef !important;
  border: 1px solid #c3decb !important;
  padding: 4px 10px !important;
  border-radius: 6px !important;
  display: inline-block !important;
  letter-spacing: 0.1px !important;
}

/* Expanders */
[data-testid="stExpander"] {
  background: var(--canvas) !important;
  border: 1px solid var(--hairline) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: 0 1px 2px rgba(17, 28, 22, 0.02) !important;
  overflow: hidden !important;
}

[data-testid="stExpander"] summary {
  font-weight: 600 !important;
  color: var(--ink) !important;
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 8px !important;
  border-bottom: 1px solid var(--hairline) !important;
  background: transparent !important;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
  font-size: 13.5px !important;
  color: var(--ink-mute) !important;
  font-weight: 500 !important;
  padding: 8px 16px !important;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
  background: transparent !important;
  border: none !important;
}

[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
  color: #15803d !important;
  font-weight: 600 !important;
  border-bottom: 2px solid #15803d !important;
}

/* Dataframe */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
  border: 1px solid var(--hairline) !important;
  border-radius: var(--radius-md) !important;
  background: var(--canvas) !important;
  box-shadow: 0 1px 2px rgba(17, 28, 22, 0.02) !important;
}

/* Progress Bar */
[data-testid="stProgress"] > div > div > div > div {
  background-color: #15803d !important;
}

/* Dividers */
hr {
  margin: 1rem 0 !important;
  border-color: var(--hairline) !important;
}

/* Footer */
.footer {
  color: var(--ink-mute);
  font-size: 0.78rem;
  text-align: center;
  margin-top: 12px !important;
  padding-top: 14px;
  border-top: 1px solid var(--hairline);
}

/* ================================================================= Practical Farmer Action Guide Card */
.farmer-guide-box {
  background: #ffffff;
  border: 1px solid #dce5de;
  border-radius: 10px;
  padding: 14px 18px;
  margin: 8px 0 14px 0;
  box-shadow: 0 1px 2px rgba(17, 28, 22, 0.03);
}

.farmer-guide-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #edf2ee;
}

.farmer-guide-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  font-weight: 700;
  color: #111c16;
}

.farmer-guide-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 6px;
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

.farmer-guide-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 900px) {
  .farmer-guide-grid {
    grid-template-columns: 1fr;
  }
}

.farmer-guide-item {
  background: #f8faf8;
  border: 1px solid #e6eee8;
  border-radius: 8px;
  padding: 11px 14px;
}

.farmer-guide-item-top {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 700;
  color: #111c16;
  margin-bottom: 4px;
}

.farmer-guide-item-desc {
  font-size: 12px;
  color: #2c3e35;
  line-height: 1.45;
}

/* Step-by-step Photo Guide */
.photo-steps-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 8px 0 16px 0;
}

.photo-step-card {
  background: #ffffff;
  border: 1px solid #dce5de;
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.photo-step-num {
  width: 24px;
  height: 24px;
  min-width: 24px;
  border-radius: 6px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #15803d;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1px;
}

.photo-step-title {
  font-size: 13px;
  font-weight: 600;
  color: #111c16;
  margin-bottom: 2px;
}

.photo-step-sub {
  font-size: 12px;
  color: #5c6f64;
  line-height: 1.4;
}

/* Pending Action / Ready Prompt Card */
.pending-action-box {
  background: #ffffff;
  border: 1px dashed #86efac;
  border-radius: 10px;
  padding: 24px 20px;
  margin: 10px 0 16px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  box-shadow: 0 1px 2px rgba(17, 28, 22, 0.02);
}

.pending-action-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #15803d;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.pending-action-title {
  font-size: 15px;
  font-weight: 700;
  color: #111c16;
  margin-bottom: 4px;
}

.pending-action-sub {
  font-size: 13px;
  color: #5c6f64;
  max-width: 560px;
  line-height: 1.45;
}

/* AI Agronomic Multi-Paragraph Narrative Card */
.ai-narrative-box {
  background: #ffffff;
  border: 1px solid #d5e0d8;
  border-left: 4px solid #15803d;
  border-radius: 12px;
  padding: 20px 24px;
  margin: 14px 0 18px 0;
  box-shadow: 0 2px 10px rgba(17, 28, 22, 0.04);
}

.ai-narrative-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  margin-bottom: 14px;
  border-bottom: 1px solid #edf2ee;
  flex-wrap: wrap;
}

.ai-narrative-title {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 15.5px;
  font-weight: 700;
  color: #111c16;
  letter-spacing: -0.01em;
}

.ai-narrative-badge {
  font-size: 11px;
  font-weight: 700;
  color: #15803d;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  padding: 4px 10px;
  border-radius: 999px;
  letter-spacing: 0.02em;
}

.ai-narrative-body p {
  font-size: 13.8px !important;
  line-height: 1.72 !important;
  color: #24352c !important;
  margin: 0 0 13px 0 !important;
  text-align: justify;
}

.ai-narrative-body p:last-child {
  margin-bottom: 0 !important;
}

.ai-narrative-body strong {
  color: #111c16;
  font-weight: 600;
}

/* Styled Bordered Cards in Streamlit 1.66+ */
div[class*="st-key-card_"] {
  background-color: #ffffff !important;
  border: 1px solid #d5e2d9 !important;
  border-radius: 10px !important;
  padding: 12px 16px !important;
  margin-bottom: 12px !important;
  box-shadow: 0 1px 3px rgba(17, 28, 22, 0.03) !important;
}

div[class*="st-key-card_"] [data-testid="stMarkdownContainer"] {
  margin-bottom: 0 !important;
}

.action-bar-info {
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  font-size: 12.5px !important;
  color: #2c3e35 !important;
  background-color: #f4faf6 !important;
  border: 1px solid #d8ebe0 !important;
  padding: 6px 12px !important;
  border-radius: 8px !important;
  line-height: 1.4 !important;
  box-sizing: border-box !important;
}

.action-bar-info strong {
  color: #14532d !important;
  font-weight: 700 !important;
}

/* ================================================================= Responsive Design for Android, iOS & Tablet */
html, body, .stApp {
  overflow-x: hidden !important;
  -webkit-text-size-adjust: 100% !important;
}

@media (max-width: 1024px) {
  .block-container,
  [data-testid="stMainBlockContainer"] {
    padding-top: 1.2rem !important;
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
    padding-bottom: 2.2rem !important;
  }
  .kpi-grid.cols-5,
  .kpi-grid.cols-4,
  .kpi-grid.cols-3 {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
  .kpi-grid.cols-5 > .kpi:last-child,
  .kpi-grid.cols-3 > .kpi:last-child {
    grid-column: 1 / -1 !important;
  }
}

@media (max-width: 768px) {
  /* Beri ruang atas untuk tombol buka sidebar mengambang agar tidak menutupi judul */
  .block-container,
  [data-testid="stMainBlockContainer"] {
    padding-top: 3.4rem !important;
    padding-left: 0.85rem !important;
    padding-right: 0.85rem !important;
    padding-bottom: 2rem !important;
  }

  /* Tombol mengambang buka sidebar di layar HP */
  [data-testid="stExpandSidebarButton"],
  [data-testid="stExpandSidebarButton"] button,
  button[data-testid="stExpandSidebarButton"],
  [data-testid="stSidebarCollapsedControl"],
  [data-testid="collapsedControl"] {
    top: 10px !important;
    left: 10px !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    min-height: 36px !important;
  }

  /* Sidebar Drawer pada Android & iOS */
  section[data-testid="stSidebar"]:not([data-collapsed="true"]):not([aria-expanded="false"]),
  [data-testid="stSidebar"]:not([data-collapsed="true"]):not([aria-expanded="false"]) {
    width: 272px !important;
    min-width: 272px !important;
    max-width: 84vw !important;
    box-shadow: 4px 0 24px rgba(17, 28, 22, 0.16) !important;
  }

  /* Hero Header di Layar HP */
  .hero {
    flex-direction: column !important;
    align-items: flex-start !important;
    padding: 14px 15px !important;
    gap: 10px !important;
    margin-bottom: 12px !important;
  }
  .hero-left {
    gap: 11px !important;
    width: 100% !important;
  }
  .hero-icon-box {
    width: 38px !important;
    height: 38px !important;
    min-width: 38px !important;
  }
  .hero-title {
    font-size: 16px !important;
    line-height: 1.3 !important;
  }
  .hero-sub {
    font-size: 12px !important;
    line-height: 1.4 !important;
  }
  .hero-right {
    display: flex !important;
    width: 100% !important;
    justify-content: flex-start !important;
  }
  .hero-status-pill {
    font-size: 10.5px !important;
    padding: 3px 10px !important;
  }

  /* Kartu Kontrol & Kolom Bertumpuk Rapi di HP */
  div[class*="st-key-card_"] {
    padding: 13px 14px !important;
    border-radius: 10px !important;
    margin-bottom: 12px !important;
  }

  [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 8px !important;
  }

  [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] > div {
    width: 100% !important;
    flex: 1 1 100% !important;
    min-width: 100% !important;
  }

  /* Badge Info & Tombol Aksi Lebar Penuh (Mudah Diketuk Jari di Android/iOS) */
  .action-bar-info {
    display: flex !important;
    flex-wrap: wrap !important;
    width: 100% !important;
    box-sizing: border-box !important;
    font-size: 12px !important;
    padding: 7px 11px !important;
  }

  div[class*="apply_btn"] .stButton,
  .st-key-btn_cls_run .stButton,
  .st-key-btn_fc_run .stButton,
  .st-key-btn_cnn_run .stButton,
  .st-key-btn_scan_run .stButton {
    justify-content: stretch !important;
    width: 100% !important;
  }

  div[class*="apply_btn"] button,
  .st-key-btn_cls_run button,
  .st-key-btn_fc_run button,
  .st-key-btn_cnn_run button,
  .st-key-btn_scan_run button,
  .stDownloadButton > button {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    height: 40px !important;
    min-height: 40px !important;
    max-height: 40px !important;
  }

  /* Kartu KPI 2 Kolom Kompak di Layar HP */
  .kpi-grid,
  .kpi-grid.cols-5,
  .kpi-grid.cols-4,
  .kpi-grid.cols-3,
  .kpi-grid.cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 9px !important;
  }
  .kpi {
    padding: 12px 13px !important;
    min-height: 90px !important;
  }
  .kpi-label {
    font-size: 10px !important;
    white-space: normal !important;
    line-height: 1.25 !important;
  }
  .kpi-value {
    font-size: 18px !important;
  }
  .kpi-sub {
    font-size: 10.5px !important;
    white-space: normal !important;
    line-height: 1.3 !important;
  }

  /* Bar Legenda & Header Bagian */
  .legend-strip {
    flex-direction: column !important;
    align-items: flex-start !important;
    padding: 10px 12px !important;
    gap: 8px !important;
  }
  .sec-header-bar {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 6px !important;
  }
  .sec-header-title {
    font-size: 14.5px !important;
  }

  /* Konsol Live Telemetry, Panduan Petani, Langkah Foto & Narasi AI */
  .live-console-card {
    padding: 13px 14px !important;
  }
  .live-console-top {
    flex-direction: column !important;
    align-items: flex-start !important;
  }
  .live-prog-wrap {
    width: 100% !important;
    min-width: 0 !important;
  }
  .live-metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 9px !important;
  }
  .live-metric-box {
    padding: 10px 12px !important;
  }
  .live-metric-val {
    font-size: 17px !important;
  }

  .farmer-guide-grid,
  .photo-steps-grid {
    grid-template-columns: 1fr !important;
    gap: 8px !important;
  }

  .ai-narrative-box {
    padding: 15px 16px !important;
  }
  .ai-narrative-title {
    font-size: 14px !important;
  }
  .ai-narrative-body p {
    font-size: 13px !important;
    line-height: 1.65 !important;
    text-align: left !important;
  }

  /* Cegah iOS Safari Auto-Zoom saat Mengetuk Input/Select */
  [data-testid="stSelectbox"] input,
  [data-testid="stMultiSelect"] input,
  [data-testid="stNumberInput"] input,
  [data-testid="stTextInput"] input,
  [data-testid="stChatInput"] textarea {
    font-size: 16px !important;
  }

  /* Asisten Kebun AI di Layar HP */
  .st-key-chat_main_card {
    margin: 0 !important;
    max-width: 100% !important;
  }
  .st-key-chat_header_row {
    padding: 10px 14px !important;
  }
  .st-key-chat_scroll_area {
    padding: 12px !important;
  }
  .st-key-chat_input_section {
    padding: 10px 12px 12px 12px !important;
  }
  [class*="st-key-sug_card_"] button,
  .st-key-chat_main_card .st-key-chat_scroll_area .stButton > button {
    height: auto !important;
    min-height: 46px !important;
    padding: 10px 12px !important;
    font-size: 12.5px !important;
  }
}

@media (max-width: 400px) {
  .kpi-grid,
  .kpi-grid.cols-5,
  .kpi-grid.cols-4,
  .kpi-grid.cols-3,
  .kpi-grid.cols-2,
  .live-metrics-grid {
    grid-template-columns: 1fr !important;
  }
}

/* ================================================================= 4-Day Forecast Visual Plant Cards & LSTM Stage Card */
.fc-plant-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin: 10px 0 18px 0;
}

.fc-plant-card {
  background: #ffffff;
  border: 1px solid #d5e2d9;
  border-radius: 14px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 2px 6px rgba(17, 28, 22, 0.04);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  position: relative;
  overflow: hidden;
}

.fc-plant-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(21, 128, 61, 0.09);
  border-color: #86efac;
}

.fc-plant-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.fc-day-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.fc-day-main {
  font-size: 13.5px;
  font-weight: 800;
  color: #14532d;
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.fc-day-sub {
  font-size: 10px;
  font-weight: 700;
  color: #15803d;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  padding: 1px 6px;
  border-radius: 999px;
  display: inline-block;
  width: fit-content;
  line-height: 1.2;
}

.fc-day-badge {
  font-size: 12px;
  font-weight: 700;
  color: #14532d;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  padding: 3px 9px;
  border-radius: 999px;
  white-space: nowrap;
}

.fc-stage-pill {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 999px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fc-growth-desc {
  font-size: 11px;
  font-weight: 700;
  color: #166534;
  background: #f4fbf6;
  border: 1px solid #dcfce7;
  border-radius: 6px;
  padding: 4px 8px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.fc-info-note {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 12px;
  color: #166534;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
  line-height: 1.45;
}

.fc-plant-visual {
  background: linear-gradient(180deg, #f4fbf6 0%, #ebf7ef 100%);
  border: 1px solid #dcfce7;
  border-radius: 11px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.fc-plant-img-wrap {
  width: 100%;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 9px;
  margin-bottom: 8px;
  background: #f4fbf6;
  border: 1px solid #cce8d5;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.fc-plant-img-wrap img {
  max-width: 96%;
  max-height: 96%;
  object-fit: contain;
  transform-origin: bottom center;
  display: block;
  transition: transform 0.25s ease;
}

.fc-plant-card:hover .fc-plant-img-wrap img {
  filter: brightness(1.03);
}

.fc-plant-svg-wrap {
  width: 124px;
  height: 118px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fc-mat-row {
  width: 100%;
  margin-top: 4px;
}

.fc-mat-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
  color: #2c3e35;
  margin-bottom: 3px;
}

.fc-mat-track {
  width: 100%;
  height: 6px;
  background: #d8ebe0;
  border-radius: 999px;
  overflow: hidden;
}

.fc-mat-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.3s ease;
}

.fc-stage-title {
  font-size: 14px;
  font-weight: 700;
  color: #111c16;
  text-align: center;
  margin: 2px 0 0 0;
}

.fc-metrics-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 7px;
  padding-top: 6px;
  border-top: 1px solid #edf2ee;
}

.fc-metric-box {
  background: #f8fbf9;
  border: 1px solid #e4ede7;
  border-radius: 8px;
  padding: 6px 8px;
}

.fc-metric-lbl {
  font-size: 10.5px;
  font-weight: 600;
  color: #52665b;
  display: flex;
  align-items: center;
  gap: 4px;
}

.fc-metric-val {
  font-size: 13px;
  font-weight: 700;
  color: #111c16;
  margin-top: 1px;
}

.fc-morph-footer {
  background: #f4faf6;
  border: 1px solid #d8ebe0;
  border-radius: 8px;
  padding: 6px 9px;
  font-size: 11.5px;
  color: #24352c;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

/* LSTM Current Stage Visual Hero Card */
.lstm-visual-hero {
  background: #ffffff;
  border: 1px solid #d5e2d9;
  border-radius: 14px;
  padding: 18px 20px;
  margin: 12px 0 16px 0;
  display: grid;
  grid-template-columns: 210px minmax(0, 1fr);
  gap: 20px;
  align-items: center;
  box-shadow: 0 2px 8px rgba(17, 28, 22, 0.04);
}

.lstm-visual-left {
  background: linear-gradient(180deg, #f2fbf5 0%, #e6f6ec 100%);
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  padding: 12px 10px 12px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.lstm-plant-img-wrap {
  width: 100%;
  height: 145px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 9px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.lstm-plant-img-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.lstm-visual-right {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lstm-visual-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.lstm-visual-stage {
  font-size: 20px;
  font-weight: 800;
  color: #111c16;
  letter-spacing: -0.02em;
}

.lstm-visual-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.lstm-visual-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.lstm-stat-item {
  background: #f8fbf9;
  border: 1px solid #e2ece5;
  border-radius: 9px;
  padding: 8px 11px;
}

.lstm-stat-lbl {
  font-size: 11px;
  font-weight: 600;
  color: #52665b;
}

.lstm-stat-val {
  font-size: 14px;
  font-weight: 700;
  color: #111c16;
  margin-top: 2px;
}

@media (max-width: 1024px) {
  .fc-plant-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
  .lstm-visual-hero {
    grid-template-columns: 180px minmax(0, 1fr) !important;
  }
  .lstm-visual-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}

@media (max-width: 640px) {
  .fc-plant-grid {
    grid-template-columns: 1fr !important;
  }
  .lstm-visual-hero {
    grid-template-columns: 1fr !important;
  }
}
</style>
"""


def inject_css():
    st.session_state.pop("theme_mode", None)
    st.markdown(CSS, unsafe_allow_html=True)


def _e(x):
    return html.escape(str(x))


def hero(title, subtitle, icon_name="sprout", badge_text="Sistem Aktif · LSTM + CNN"):
    clean_title = strip_emoji(title)
    icon_svg = icon(icon_name, 20, color="#15803d")
    st.markdown(
        f'<div class="hero">'
        f'<div class="hero-left">'
        f'<div class="hero-icon-box">{icon_svg}</div>'
        f'<div class="hero-text">'
        f'<div class="hero-title">{_e(clean_title)}</div>'
        f'<div class="hero-sub">{_e(subtitle)}</div>'
        f'</div>'
        f'</div>'
        f'<div class="hero-right">'
        f'<span class="hero-status-pill"><span class="hero-status-dot"></span>{_e(badge_text)}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_header(title, subtitle="", icon_name="layers", right_html=""):
    """Header bagian halaman dengan judul di kiri dan badge/status di kanan."""
    clean_title = strip_emoji(title)
    ic = icon(icon_name, 17, color="#15803d") if icon_name else ""
    sub_html = f'<div class="sec-header-sub">{_e(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div class="sec-header-bar">'
        f'<div class="sec-header-left">'
        f'<div class="sec-header-title">{ic}<span>{_e(clean_title)}</span></div>'
        f'{sub_html}'
        f'</div>'
        f'<div>{right_html}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def maturity_legend_bar(th):
    """Bar legenda ringkas untuk menjelaskan skala tingkat kematangan pakcoy."""
    st.markdown(
        f'<div class="legend-strip">'
        f'<div class="legend-strip-left">{icon("info", 15, color="#15803d")}<span>Panduan Skala Kematangan Tanaman:</span></div>'
        f'<div class="legend-pills">'
        f'<span class="legend-pill"><span class="legend-dot" style="background:#0d9488;"></span><strong>Masa Pertumbuhan:</strong> &lt; {th[0]:.1f}%</span>'
        f'<span class="legend-pill"><span class="legend-dot" style="background:#d97706;"></span><strong>Mendekati Panen:</strong> {th[0]:.1f}% – {th[1]:.1f}%</span>'
        f'<span class="legend-pill"><span class="legend-dot" style="background:#15803d;"></span><strong>Siap Panen:</strong> &ge; {th[1]:.1f}%</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def kpi_html(items, cols=None):
    """items: list of dict(icon, label, value, color, sub)."""
    n = len(items)
    if cols is None:
        if n == 5:
            cols_cls = "cols-5"
        elif n == 4:
            cols_cls = "cols-4"
        elif n in (3, 6):
            cols_cls = "cols-3"
        elif n == 2:
            cols_cls = "cols-2"
        else:
            cols_cls = ""
    else:
        cols_cls = f"cols-{cols}"

    cards = []
    for it in items:
        raw_color = it.get("color", "")
        if raw_color in ("#ea2261", "#dc2626", "#f87171"):
            accent_color = "#dc2626"
            icon_bg = "#fef2f2"
            icon_border = "#fecaca"
            val_color = "#b91c1c"
        elif raw_color in ("#fb923c", "#facc15", "#9b6829", "#d97706"):
            accent_color = "#d97706"
            icon_bg = "#fffbeb"
            icon_border = "#fde68a"
            val_color = "#111c16"
        elif raw_color in ("#38bdf8", "#60a5fa", "#0284c7"):
            accent_color = "#0d9488"
            icon_bg = "#f0fdfa"
            icon_border = "#99f6e4"
            val_color = "#111c16"
        elif raw_color == "#94a3b8":
            accent_color = "#64748b"
            icon_bg = "#f1f5f9"
            icon_border = "#cbd5e1"
            val_color = "#475569"
        else:
            accent_color = "#15803d"
            icon_bg = "#f0fdf4"
            icon_border = "#bbf7d0"
            val_color = "#111c16"

        raw_icon = it.get("icon", "")
        icon_name = ICON_MAP.get(raw_icon, raw_icon) if raw_icon else ""
        icon_html = (
            f'<div class="kpi-icon-pill" style="background:{icon_bg};color:{accent_color};border:1px solid {icon_border};">'
            f'{icon(icon_name, 15, color=accent_color)}</div>'
        ) if icon_name else ""
        sub = f'<div class="kpi-sub">{_e(strip_emoji(it["sub"]))}</div>' if it.get("sub") else ""
        clean_val = strip_emoji(it["value"])
        clean_lbl = strip_emoji(it["label"])
        cards.append(
            f'<div class="kpi">'
            f'<div class="kpi-top"><span class="kpi-label" title="{_e(clean_lbl)}">{_e(clean_lbl)}</span>{icon_html}</div>'
            f'<div class="kpi-value" style="color:{val_color}" title="{_e(clean_val)}">{_e(clean_val)}</div>'
            f'{sub}'
            f'</div>'
        )
    return f'<div class="kpi-grid {cols_cls}">' + "".join(cards) + "</div>"


def kpi_cards(items, container=None, cols=None):
    (container or st).markdown(kpi_html(items, cols=cols), unsafe_allow_html=True)


def banner_html(kind, text):
    icon_map = {
        "ok": "check-circle",
        "warn": "alert-triangle",
        "danger": "x-circle",
        "info": "info"
    }
    icon_svg = icon(icon_map.get(kind, "info"), 18, color="currentColor")
    clean_text = strip_emoji(text)
    return (
        f'<div class="banner {kind}">'
        f'<div class="banner-icon">{icon_svg}</div>'
        f'<div class="banner-text">{_e(clean_text)}</div>'
        f'</div>'
    )


def banner(kind, text, container=None):
    (container or st).markdown(banner_html(kind, text), unsafe_allow_html=True)


def live_badge_html(active=True):
    cls = "live-badge" if active else "live-badge paused"
    txt = "LIVE TELEMETRY" if active else "SIMULASI DIJEDA"
    return f'<span class="{cls}"><span class="live-dot"></span>{txt}</span>'


def live_badge(active=True):
    st.markdown(live_badge_html(active), unsafe_allow_html=True)


def chips(items, container=None):
    """items: list of (teks, aktif)."""
    rows = []
    for t, on in items:
        status_text = "Siap" if on else "Belum aktif"
        status_cls = "ready" if on else "not-ready"
        clean_t = strip_emoji(t)
        rows.append(
            f'<div class="model-status-row">'
            f'<div class="model-status-left">'
            f'<span class="model-dot {status_cls}"></span>'
            f'<span class="model-name">{_e(clean_t)}</span>'
            f'</div>'
            f'<span class="model-status-text {status_cls}">{status_text}</span>'
            f'</div>'
        )
    html_status = '<div class="model-status-box">' + "".join(rows) + '</div>'
    (container or st).markdown(html_status, unsafe_allow_html=True)


def footer():
    st.markdown('<div class="footer">Smart Farming Pakcoy · Sistem Monitoring &amp; Analitik Budidaya Tanaman Pakcoy (LSTM + CNN)</div>',
                unsafe_allow_html=True)


def _compute_action_advice(moist, temp, mat, stage_label, dry=55.0, wet=76.0):
    m_val = float(moist)
    t_val = float(temp)
    mat_val = float(mat)

    if m_val < dry:
        water_status = "Tanah Kering — Perlu Penyiraman"
        water_color = "#dc2626"
        water_bg = "#fef2f2"
        water_advice = f"Kelembapan ({m_val:.0f}%) di bawah batas aman ({dry:.0f}%). Segera nyalakan pompa air hingga mencapai kisaran ideal 60–75%."
    elif m_val >= wet:
        water_status = "Tanah Basah — Hentikan Air"
        water_color = "#0284c7"
        water_bg = "#f0f9ff"
        water_advice = f"Kelembapan ({m_val:.0f}%) melebihi batas basah ({wet:.0f}%). Matikan pompa dan periksa drainase agar akar tidak membusuk."
    else:
        water_status = "Kelembapan Tanah Ideal"
        water_color = "#15803d"
        water_bg = "#f0fdf4"
        water_advice = f"Kelembapan ({m_val:.0f}%) berada di zona ideal ({dry:.0f}–{wet:.0f}%). Tidak perlu penyiraman tambahan saat ini."

    if t_val > 30.0:
        temp_status = "Udara Cukup Terik"
        temp_color = "#d97706"
        temp_bg = "#fffbeb"
        temp_advice = f"Suhu ({t_val:.1f}°C) tergolong hangat. Pastikan sirkulasi udara atau paranet/naungan memadai agar daun tidak layu."
    elif t_val < 18.0:
        temp_status = "Udara Cukup Sejuk"
        temp_color = "#0284c7"
        temp_bg = "#f0f9ff"
        temp_advice = f"Suhu ({t_val:.1f}°C) relatif dingin. Pantau kelembapan daun agar tidak terlalu lembap di pagi/malam hari."
    else:
        temp_status = "Suhu Lingkungan Nyaman"
        temp_color = "#15803d"
        temp_bg = "#f0fdf4"
        temp_advice = f"Suhu ({t_val:.1f}°C) berada di rentang optimal bagi fotosintesis dan pembentukan daun pakcoy."

    st_clean = strip_emoji(stage_label)
    if "Siap Panen" in st_clean or mat_val >= 89.0:
        crop_status = f"Fase: {st_clean} ({mat_val:.0f}%)"
        crop_color = "#15803d"
        crop_bg = "#f0fdf4"
        crop_advice = "Tanaman pakcoy sudah matang optimal. Disarankan segera panen dalam 1–2 hari agar tangkai tetap segar dan renyah."
    elif "Mendekati" in st_clean or mat_val >= 66.5:
        crop_status = f"Fase: {st_clean} ({mat_val:.0f}%)"
        crop_color = "#d97706"
        crop_bg = "#fffbeb"
        crop_advice = "Rumpun daun mulai memadat. Jaga kestabilan air dan bersiap memasuki jadwal panen beberapa hari ke depan."
    else:
        crop_status = f"Fase: {st_clean} ({mat_val:.0f}%)"
        crop_color = "#0d9488"
        crop_bg = "#f0fdfa"
        crop_advice = "Tanaman dalam masa pertumbuhan daun (vegetatif). Fokuskan pada kecukupan sinar matahari, air, dan pantau hama."

    return {
        "water": (water_status, water_color, water_bg, water_advice),
        "temp": (temp_status, temp_color, temp_bg, temp_advice),
        "crop": (crop_status, crop_color, crop_bg, crop_advice),
    }


def action_guide_card(moist, temp, mat, stage_label, dry=55.0, wet=76.0, title="Panduan Tindakan Kebun Saat Ini", badge_text="Saran Otomatis"):
    """Kartu ringkasan tindakan praktis untuk petani/orang awam berdasarkan angka sensor & kematangan."""
    adv = _compute_action_advice(moist, temp, mat, stage_label, dry=dry, wet=wet)
    water_status, water_color, _, water_advice = adv["water"]
    temp_status, temp_color, _, temp_advice = adv["temp"]
    crop_status, crop_color, _, crop_advice = adv["crop"]

    html_out = (
        f'<div class="farmer-guide-box">'
        f'<div class="farmer-guide-header">'
        f'<div class="farmer-guide-title">{icon("sprout", 17, color="#15803d")}<span>{_e(title)}</span></div>'
        f'<span class="farmer-guide-badge">{_e(badge_text)}</span>'
        f'</div>'
        f'<div class="farmer-guide-grid">'
        f'<div class="farmer-guide-item">'
        f'<div class="farmer-guide-item-top" style="color:{water_color};">{icon("droplets", 15, color=water_color)}<span>{_e(water_status)}</span></div>'
        f'<div class="farmer-guide-item-desc">{_e(water_advice)}</div>'
        f'</div>'
        f'<div class="farmer-guide-item">'
        f'<div class="farmer-guide-item-top" style="color:{temp_color};">{icon("thermometer", 15, color=temp_color)}<span>{_e(temp_status)}</span></div>'
        f'<div class="farmer-guide-item-desc">{_e(temp_advice)}</div>'
        f'</div>'
        f'<div class="farmer-guide-item">'
        f'<div class="farmer-guide-item-top" style="color:{crop_color};">{icon("check-circle", 15, color=crop_color)}<span>{_e(crop_status)}</span></div>'
        f'<div class="farmer-guide-item-desc">{_e(crop_advice)}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html_out, unsafe_allow_html=True)


def live_telemetry_console(day, cycle_days, jam_str, step_idx, total_steps, moist, temp, cond_str, mat, stage_str, stage_source, dry=55.0, wet=76.0):
    """Konsol telemetri live terpadu: status header + progress bar + 4 kartu metrik proporsional + 3 rekomendasi tindakan."""
    adv = _compute_action_advice(moist, temp, mat, stage_str, dry=dry, wet=wet)
    water_status, water_color, water_bg, water_advice = adv["water"]
    temp_status, temp_color, temp_bg, temp_advice = adv["temp"]
    crop_status, crop_color, crop_bg, crop_advice = adv["crop"]

    pct_prog = min(100, max(1, int(round((step_idx / max(1, total_steps)) * 100))))

    html_out = (
        f'<div class="live-console-card">'
        # 1. Top Console Bar
        f'<div class="live-console-top">'
        f'<div class="live-console-meta">'
        f'<span class="live-meta-pill">{icon("calendar", 14, color="#15803d")}<span>Hari ke-{int(day)} dari {int(cycle_days)} &middot; {_e(jam_str)}</span></span>'
        f'<span class="live-meta-step"> Pembacaan Sensor #{step_idx} dari {total_steps}</span>'
        f'</div>'
        f'<div class="live-prog-wrap">'
        f'<span class="live-meta-step">Progres Siklus:</span>'
        f'<div class="live-prog-track"><div class="live-prog-fill" style="width:{pct_prog}%;"></div></div>'
        f'<span class="live-prog-pct">{pct_prog}%</span>'
        f'</div>'
        f'</div>'
        # 2. 4 Spacious Telemetry Metrics
        f'<div class="live-metrics-grid">'
        # Metric 1: Kelembapan Tanah
        f'<div class="live-metric-box">'
        f'<div class="live-metric-head">'
        f'<span class="live-metric-lbl">Kelembapan Tanah</span>'
        f'<span class="live-metric-badge" style="background:{water_bg};color:{water_color};">{_e(cond_str)}</span>'
        f'</div>'
        f'<div class="live-metric-val">{float(moist):.0f}%</div>'
        f'<div class="live-metric-sub">Rentang ideal: {dry:.0f}% &ndash; {wet:.0f}%</div>'
        f'</div>'
        # Metric 2: Suhu Udara
        f'<div class="live-metric-box">'
        f'<div class="live-metric-head">'
        f'<span class="live-metric-lbl">Suhu Udara Kebun</span>'
        f'<span class="live-metric-badge" style="background:{temp_bg};color:{temp_color};">Ideal 20&ndash;30&deg;C</span>'
        f'</div>'
        f'<div class="live-metric-val">{float(temp):.1f}&deg;C</div>'
        f'<div class="live-metric-sub">{_e(temp_status)}</div>'
        f'</div>'
        # Metric 3: Tingkat Kematangan
        f'<div class="live-metric-box">'
        f'<div class="live-metric-head">'
        f'<span class="live-metric-lbl">Tingkat Kematangan</span>'
        f'<span class="live-metric-badge" style="background:{crop_bg};color:{crop_color};">Panen &ge; 89%</span>'
        f'</div>'
        f'<div class="live-metric-val">{float(mat):.0f}%</div>'
        f'<div class="live-metric-sub">Skala 0% (Bibit) s.d. 100% (Panen)</div>'
        f'</div>'
        # Metric 4: Fase Pertumbuhan
        f'<div class="live-metric-box">'
        f'<div class="live-metric-head">'
        f'<span class="live-metric-lbl">Fase Tanaman</span>'
        f'<span class="live-metric-badge" style="background:#f0fdf4;color:#15803d;">AI LSTM</span>'
        f'</div>'
        f'<div class="live-metric-val" style="font-size:17.5px;">{_e(strip_emoji(stage_str))}</div>'
        f'<div class="live-metric-sub">{_e(stage_source)}</div>'
        f'</div>'
        f'</div>'
        # 3. Integrated 3-Column Action Guide
        f'<div class="farmer-guide-grid">'
        f'<div class="farmer-guide-item">'
        f'<div class="farmer-guide-item-top" style="color:{water_color};">{icon("droplets", 14, color=water_color)}<span>{_e(water_status)}</span></div>'
        f'<div class="farmer-guide-item-desc">{_e(water_advice)}</div>'
        f'</div>'
        f'<div class="farmer-guide-item">'
        f'<div class="farmer-guide-item-top" style="color:{temp_color};">{icon("thermometer", 14, color=temp_color)}<span>{_e(temp_status)}</span></div>'
        f'<div class="farmer-guide-item-desc">{_e(temp_advice)}</div>'
        f'</div>'
        f'<div class="farmer-guide-item">'
        f'<div class="farmer-guide-item-top" style="color:{crop_color};">{icon("check-circle", 14, color=crop_color)}<span>{_e(crop_status)}</span></div>'
        f'<div class="farmer-guide-item-desc">{_e(crop_advice)}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html_out, unsafe_allow_html=True)


def photo_guide_card():
    """Menampilkan 3 langkah mudah memotret tanaman pakcoy untuk orang awam."""
    html_out = (
        '<div class="photo-steps-grid">'
        '<div class="photo-step-card">'
        '<div class="photo-step-num">1</div>'
        '<div><div class="photo-step-title">Foto dari Sudut Atas</div>'
        '<div class="photo-step-sub">Arahkan kamera tegak lurus dari atas tanaman (jarak ±30–40 cm) agar seluruh mekar daun terlihat.</div></div>'
        '</div>'
        '<div class="photo-step-card">'
        '<div class="photo-step-num">2</div>'
        '<div><div class="photo-step-title">Pencahayaan Cukup</div>'
        '<div class="photo-step-sub">Pastikan cahaya merata dan tidak tertutup bayangan gelap agar warna hijau daun terbaca akurat.</div></div>'
        '</div>'
        '<div class="photo-step-card">'
        '<div class="photo-step-num">3</div>'
        '<div><div class="photo-step-title">Fokus pada 1 Tanaman</div>'
        '<div class="photo-step-sub">Usahakan satu rumpun pakcoy berada di tengah foto dan tidak tercampur objek lain.</div></div>'
        '</div>'
        '</div>'
    )
    st.markdown(html_out, unsafe_allow_html=True)


def pending_action_card(title, subtitle, icon_name="play"):
    """Kartu penunjuk profesional saat pengguna memilih siklus/parameter dan perlu menekan tombol aksi."""
    st.markdown(
        f'<div class="pending-action-box">'
        f'<div class="pending-action-icon">{icon(icon_name, 20, color="#15803d")}</div>'
        f'<div class="pending-action-title">{_e(title)}</div>'
        f'<div class="pending-action-sub">{_e(subtitle)}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def compute_pakcoy_leaf_metrics(g, stage_key="masa_pertumbuhan", manual_scale=0.0):
    """Menghitung ukuran fisik daun pakcoy asli (panjang daun cm, lebar daun cm, luas helaian daun cm²,
    diameter tajuk rumpun cm, dan indeks klorofil SPAD) sesuai standar agronomi Brassica rapa subsp. chinensis."""
    cov = float(g.get("coverage_pct") or 0.0)
    comp = float(g.get("compactness") or 0.0)
    grn = float(g.get("greenness") or 0.0)
    bw = float(g.get("bbox_w_px") or 1.0)
    bh = float(g.get("bbox_h_px") or 1.0)

    # Standar ukuran biologis tanaman pakcoy asli per fase pertumbuhan:
    # - Masa Pertumbuhan (Hari 1-18): Panjang daun 6.5-11.8 cm, Lebar daun 4.0-7.2 cm, Tajuk 9.5-14.5 cm
    # - Mendekati Panen (Hari 19-25): Panjang daun 12.5-17.5 cm, Lebar daun 7.5-10.8 cm, Tajuk 15.0-20.5 cm
    # - Siap Panen (Hari 26-30): Panjang daun 18.0-23.5 cm, Lebar daun 11.0-14.5 cm, Tajuk 21.0-26.5 cm
    stage_specs = {
        "masa_pertumbuhan": {
            "len_range": (6.5, 11.8),
            "wid_range": (4.0, 7.2),
            "canopy_range": (9.5, 14.5),
            "area_range": (18.0, 58.0),
            "k_factor": 0.68,
            "age_est": "Hari ke-7 s.d. Hari ke-18",
        },
        "mendekati_panen": {
            "len_range": (12.5, 17.5),
            "wid_range": (7.5, 10.8),
            "canopy_range": (15.0, 20.5),
            "area_range": (65.0, 132.0),
            "k_factor": 0.70,
            "age_est": "Hari ke-19 s.d. Hari ke-25",
        },
        "siap_panen": {
            "len_range": (18.0, 23.5),
            "wid_range": (11.0, 14.5),
            "canopy_range": (21.0, 26.5),
            "area_range": (140.0, 240.0),
            "k_factor": 0.72,
            "age_est": "Hari ke-26 s.d. Hari ke-30",
        },
    }
    spec = stage_specs.get(stage_key, stage_specs["masa_pertumbuhan"])

    # Faktor proporsi alami dari citra (tutupan kanopi & kerapatan tajuk pada rentang 0.0 - 1.0)
    cov_norm = min(1.0, max(0.0, (cov - 5.0) / 60.0))
    comp_norm = min(1.0, max(0.0, (comp - 0.15) / 0.65))
    blend = 0.6 * cov_norm + 0.4 * comp_norm

    # Variasi rasio bentuk bounding box agar sensitif terhadap geometri daun pada foto
    aspect_ratio = min(1.35, max(0.75, max(bw, bh) / max(1.0, min(bw, bh)) / 1.25))

    l_min, l_max = spec["len_range"]
    w_min, w_max = spec["wid_range"]
    c_min, c_max = spec["canopy_range"]

    if manual_scale and manual_scale > 0:
        # Jika pengguna memasukkan kalibrasi manual (px/cm), hitung dari ukuran piksel tajuk
        canopy_dia_cm = max(bw, bh) / float(manual_scale)
        leaf_len_cm = canopy_dia_cm * 0.78
        leaf_wid_cm = leaf_len_cm * 0.62
        leaf_area_cm2 = leaf_len_cm * leaf_wid_cm * spec["k_factor"]
    else:
        leaf_len_cm = (l_min + blend * (l_max - l_min)) * min(1.08, max(0.92, aspect_ratio))
        leaf_len_cm = float(min(l_max, max(l_min, leaf_len_cm)))
        leaf_wid_cm = w_min + (0.5 * blend + 0.5 * comp_norm) * (w_max - w_min)
        leaf_wid_cm = float(min(w_max, max(w_min, leaf_wid_cm)))
        canopy_dia_cm = c_min + blend * (c_max - c_min)
        canopy_dia_cm = float(min(c_max, max(c_min, canopy_dia_cm)))
        # Rumus luas helaian daun pakcoy standar hortikultura: LA = Panjang × Lebar × k (cm²)
        leaf_area_cm2 = float(leaf_len_cm * leaf_wid_cm * spec["k_factor"])

    # Estimasi indeks klorofil daun dalam satuan SPAD (rentang fisiologis pakcoy: 22.0 - 52.0 SPAD)
    yellow_pct = float(g.get("yellow_pct") or 0.0)
    spad_val = 24.0 + (grn / 100.0) * 28.0 - (yellow_pct * 0.18)
    spad_val = float(min(52.0, max(18.5, spad_val)))

    return {
        "leaf_len_cm": round(leaf_len_cm, 1),
        "leaf_wid_cm": round(leaf_wid_cm, 1),
        "leaf_area_cm2": round(leaf_area_cm2, 1),
        "canopy_dia_cm": round(canopy_dia_cm, 1),
        "spad_val": round(spad_val, 1),
        "len_std_str": f"{l_min:.1f}–{l_max:.1f} cm",
        "wid_std_str": f"{w_min:.1f}–{w_max:.1f} cm",
        "area_std_str": f"{spec['area_range'][0]:.0f}–{spec['area_range'][1]:.0f} cm²",
        "canopy_std_str": f"{c_min:.1f}–{c_max:.1f} cm",
        "age_est": spec["age_est"],
    }


def ai_plant_analysis_card(stage_key, stage_label, confidence, readiness_idx, metrics, g, sensor_row=None):
    """Menampilkan penjelasan lengkap AI Agronomi dalam bentuk paragraf komprehensif mengenai ukuran fisik daun,
    kesehatan klorofil, dan saran perawatan tanaman pakcoy."""
    leaf_len = metrics["leaf_len_cm"]
    leaf_wid = metrics["leaf_wid_cm"]
    leaf_area = metrics["leaf_area_cm2"]
    canopy_dia = metrics["canopy_dia_cm"]
    spad_val = metrics["spad_val"]
    age_est = metrics["age_est"]

    comp_pct = float(g.get("compactness") or 0.0) * 100.0
    yellow_pct = float(g.get("yellow_pct") or 0.0)
    green_pct = float(g.get("greenness") or 0.0)

    # Paragraf 1: Analisis Morfologi & Ukuran Fisik Daun Pakcoy Asli
    p1 = (
        f"Berdasarkan hasil pemeriksaan visual menggunakan model kecerdasan buatan (CNN MobileNetV2), tanaman pakcoy "
        f"pada foto ini teridentifikasi berada pada fase <strong>{_e(stage_label)}</strong> (perkiraan umur tanam "
        f"<strong>{_e(age_est)}</strong>) dengan tingkat keyakinan AI sebesar <strong>{confidence:.0%}</strong> dan skor "
        f"kesiapan panen <strong>{readiness_idx:.0f}/100</strong>. Dari sisi ukuran fisik morfologi tanaman pakcoy asli, "
        f"helaian daun utama memiliki <strong>panjang daun ± {leaf_len:.1f} cm</strong> (standar normal fase ini: "
        f"{metrics['len_std_str']}) dan <strong>lebar daun ± {leaf_wid:.1f} cm</strong> (standar normal: "
        f"{metrics['wid_std_str']}), sehingga menghasilkan <strong>luas permukaan per helai daun sekitar "
        f"{leaf_area:.1f} cm²</strong>. Sementara itu, bentang <strong>diameter tajuk rumpun mencapai ± {canopy_dia:.1f} cm</strong> "
        f"dengan tingkat kerapatan kanopi sebesar <strong>{comp_pct:.0f}%</strong>, yang menunjukkan bahwa susunan roset "
        f"daun {'sudah tumbuh sangat rapat dan rimbun memenuhi tajuk tanaman' if comp_pct >= 65 else ('mulai merapat membentuk struktur tajuk yang seimbang' if comp_pct >= 42 else 'masih memiliki celah antar-tangkai karena tanaman sedang aktif melebarkan helai daun muda')}."
    )

    # Paragraf 2: Evaluasi Kesehatan Daun, Kadar Klorofil (SPAD), & Gejala Menguning
    if yellow_pct >= 8.0:
        p2 = (
            f"Dari hasil analisis spektrum warna daun, terdeteksi adanya <strong>gejala daun menguning (klorosis) sebesar "
            f"{yellow_pct:.1f}%</strong> dengan indeks klorofil hijau <strong>{spad_val:.1f} SPAD</strong> (kepekatan warna hijau "
            f"<strong>{green_pct:.0f}%</strong>). Persentase warna kuning di atas 8% menandakan bahwa sebagian helai daun "
            f"mengalami penurunan zat hijau daun (klorofil). Pada budidaya pakcoy, kondisi ini umumnya dipicu oleh tiga faktor "
            f"utama: (1) kekurangan unsur hara makro terutama <strong>Nitrogen (N)</strong> atau <strong>Magnesium (Mg)</strong> "
            f"yang dibutuhkan untuk pembentukan klorofil, (2) kondisi media tanam yang terlalu lembap/becek sehingga akar kekurangan "
            f"oksigen dalam menyerap nutrisi, atau (3) kurangnya intensitas cahaya matahari pada helai daun bagian bawah."
        )
    elif yellow_pct >= 2.0:
        p2 = (
            f"Evaluasi kesehatan warna daun menunjukkan kadar klorofil sebesar <strong>{spad_val:.1f} SPAD</strong> (kepekatan "
            f"warna hijau <strong>{green_pct:.0f}%</strong>) dengan <strong>persentase daun menguning sebesar {yellow_pct:.1f}%</strong>. "
            f"Kondisi ini tergolong normal dan cukup sehat, namun terdapat sedikit warna kekuningan ringan yang umumnya berasal "
            f"dari daun tua paling bawah (<em>senescence</em> alami) atau pantulan cahaya pada tepi daun. Pertumbuhan fotosintesis "
            f"tanaman secara keseluruhan tetap berjalan baik, tetapi ketersediaan air dan nutrisi tetap perlu dijaga agar gejala "
            f"kekuningan tidak meluas ke daun muda."
        )
    else:
        p2 = (
            f"Evaluasi kesehatan warna daun menunjukkan kondisi yang <strong>sangat sehat dan prima</strong>, dengan indeks "
            f"klorofil mencapai <strong>{spad_val:.1f} SPAD</strong> (kepekatan hijau <strong>{green_pct:.0f}%</strong>) serta "
            f"persentase daun menguning yang sangat rendah yaitu hanya <strong>{yellow_pct:.1f}%</strong>. Warna hijau segar yang "
            f"merata pada permukaan lamina daun menandakan bahwa penyerapan unsur hara Nitrogen, zat besi, dan air oleh perakaran "
            f"berlangsung optimal, sehingga proses fotosintesis untuk pembentukan biomassa daun berjalan maksimal."
        )

    # Paragraf 3: Saran Tindakan Perawatan (Penyiraman, Nutrisi AB Mix / Pupuk, & Suhu)
    if stage_key == "masa_pertumbuhan":
        nutrisi_advice = (
            "berikan nutrisi pertumbuhan vegetatif (larutan <strong>AB Mix kepekatan 600–900 ppm</strong> atau "
            "<strong>EC 1,2–1,8 mS/cm</strong> untuk hidroponik, maupun pupuk cair kaya Nitrogen untuk media tanah) guna "
            "mempercepat pertambahan jumlah dan panjang helai daun"
        )
    elif stage_key == "mendekati_panen":
        nutrisi_advice = (
            "tingkatkan kepekatan nutrisi ke rentang <strong>1.000–1.200 ppm (EC 2,0–2,4 mS/cm)</strong> dengan kecukupan "
            "unsur Kalium (K) dan Kalsium (Ca) agar tangkai daun (bonggol putih) menebal dengan renyah dan bobot rumpun meningkat"
        )
    else:
        nutrisi_advice = (
            "hentikan penambahan pupuk kimia pekat dan cukup berikan air bersih bersirkulasi baik agar jaringan daun "
            "tetap segar, renyah, dan bebas dari residu nutrisi berlebih saat dipanen"
        )

    sensor_sentence = ""
    if sensor_row is not None:
        m_s = float(sensor_row.get("Soil Moisture (%)", 60.0))
        t_s = float(sensor_row.get("Temperature (°C)", 27.0))
        d_s = int(sensor_row.get("Day", 15))
        sensor_sentence = (
            f" Berdasarkan data sensor kebun saat ini pada <strong>Hari ke-{d_s}</strong>, kelembapan tanah tercatat "
            f"<strong>{m_s:.0f}%</strong> dan suhu udara <strong>{t_s:.1f}°C</strong>, sehingga Anda perlu "
            f"{'segera menyalakan penyiraman karena tanah mulai kering' if m_s < 55.0 else ('menghentikan penyiraman sementara karena tanah terlalu basah' if m_s >= 76.0 else 'mempertahankan pola penyiraman saat ini karena kelembapan tanah sudah ideal')}."
        )

    p3 = (
        f"<strong>Saran Perawatan Air, Nutrisi &amp; Lingkungan:</strong> Untuk menjaga pertumbuhan pakcoy tetap optimal, "
        f"pastikan kelembapan media tanam selalu berada pada rentang ideal <strong>55% hingga 75%</strong> dengan jadwal "
        f"penyiraman teratur pada pagi hari (pukul 07:00–08:00) dan sore hari (pukul 16:00–17:00). Selanjutnya, {nutrisi_advice}. "
        f"Jaga pH media tanam atau air nutrisi pada kisaran <strong>pH 6,0–6,8</strong> serta pertahankan suhu lingkungan "
        f"di rentang <strong>20°C–30°C</strong> dengan paparan sinar matahari minimal 4–6 jam per hari.{sensor_sentence}"
    )

    # Paragraf 4: Tindakan Sanitasi Daun, Pengendalian Hama, & Persiapan Panen
    Sanitasi_txt = (
        "Segera pangkas dan bersihkan helai daun bagian bawah yang tampak menguning atau layu menggunakan gunting bersih "
        "agar nutrisi terfokus ke daun utama dan tidak memicu kelembapan berlebih yang mengundang jamur."
        if yellow_pct >= 5.0 else
        "Pertahankan kebersihan area sekitar pangkal batang dari gulma maupun genangan air agar sirkulasi udara di sela-sela tangkai daun tetap lancar."
    )
    if stage_key == "siap_panen":
        panen_txt = (
            "Mengingat tanaman sudah memasuki fase <strong>Siap Panen</strong> dengan ukuran daun yang telah mencapai standar "
            "optimal, disarankan untuk <strong>segera melakukan pemanenan dalam 1–2 hari ke depan</strong> (paling baik dipanen "
            "pada pagi hari saat kadar air daun tinggi) sebelum tangkai menua, berserat keras, atau muncul bunga (<em>bolting</em>)."
        )
    elif stage_key == "mendekati_panen":
        panen_txt = (
            "Tanaman diperkirakan akan mencapai puncak kematangan <strong>Siap Panen dalam 5–10 hari ke depan (menuju Hari ke-30)</strong>, "
            "ketika panjang daun mencapai 18–23 cm dan bonggol putih tampak padat menutup sempurna."
        )
    else:
        panen_txt = (
            "Periksa permukaan bawah daun secara rutin setiap pagi untuk mencegah serangan hama ulat daun (<em>Plutella xylostella</em>) "
            "dan kutu daun (<em>Aphids</em>) sejak dini, sehingga tanaman dapat tumbuh mulus hingga waktu panen optimal pada <strong>Hari ke-30</strong>."
        )

    p4 = f"<strong>Tindakan Pemeliharaan Tajuk &amp; Target Panen:</strong> {Sanitasi_txt} {panen_txt}"

    html_out = (
        f'<div class="ai-narrative-box">'
        f'<div class="ai-narrative-head">'
        f'<div class="ai-narrative-title">{icon("sparkles", 18, color="#15803d")}<span>Analisis AI &amp; Rekomendasi Perawatan Tanaman Pakcoy</span></div>'
        f'<span class="ai-narrative-badge">Laporan Diagnostik AI Lengkap</span>'
        f'</div>'
        f'<div class="ai-narrative-body">'
        f'<p>{p1}</p>'
        f'<p>{p2}</p>'
        f'<p>{p3}</p>'
        f'<p>{p4}</p>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html_out, unsafe_allow_html=True)


def estimate_morphology_from_maturity(mat_pct):
    """Menghitung estimasi panjang daun (cm), lebar daun (cm), dan diameter tajuk (cm) berdasarkan persentase kematangan (0–100%)."""
    m = max(5.0, min(100.0, float(mat_pct)))
    ratio = m / 100.0
    leaf_len = round(6.0 + ratio * 16.5, 1)
    leaf_wid = round(3.8 + ratio * 9.8, 1)
    canopy_dia = round(9.0 + ratio * 16.5, 1)
    leaf_area = round(leaf_len * leaf_wid * 0.70, 1)
    return {
        "leaf_len_cm": leaf_len,
        "leaf_wid_cm": leaf_wid,
        "canopy_dia_cm": canopy_dia,
        "leaf_area_cm2": leaf_area,
    }


def pakcoy_plant_svg(stage_key="masa_pertumbuhan", maturity_pct=50.0, uid="pk", size=122):
    """Mengembalikan ilustrasi vektor botani tanaman Pakcoy (Bok Choy) berlapis yang tumbuh proporsional sesuai fase & tingkat kematangan."""
    m = max(8.0, min(100.0, float(maturity_pct)))
    scale = round(0.72 + (m / 100.0) * 0.30, 3)

    if stage_key == "siap_panen" or m >= 89.0:
        outer_leaves = (
            f'<path d="M70 98 C34 86 16 58 24 34 C31 15 54 20 64 52 C68 65 69 82 70 98 Z" fill="url(#leafDark_{uid})" />'
            f'<path d="M70 98 C106 86 124 58 116 34 C109 15 86 20 76 52 C72 65 71 82 70 98 Z" fill="url(#leafDark_{uid})" />'
            f'<path d="M70 98 C44 82 22 68 18 48 C15 32 34 26 52 50 C61 62 66 80 70 98 Z" fill="url(#leafMid_{uid})" opacity="0.92" />'
            f'<path d="M70 98 C96 82 118 68 122 48 C125 32 106 26 88 50 C79 62 74 80 70 98 Z" fill="url(#leafMid_{uid})" opacity="0.92" />'
        )
        mid_leaves = (
            f'<path d="M70 98 C42 74 36 38 48 20 C58 7 72 22 71 54 C71 70 70 85 70 98 Z" fill="url(#leafMid_{uid})" />'
            f'<path d="M70 98 C98 74 104 38 92 20 C82 7 68 22 69 54 C69 70 70 85 70 98 Z" fill="url(#leafMid_{uid})" />'
            f'<path d="M70 97 C56 68 54 30 70 16 C86 30 84 68 70 97 Z" fill="url(#leafBright_{uid})" />'
        )
        petiole_bulb = (
            f'<path d="M52 99 C45 84 46 66 54 55 C59 68 62 82 64 99 Z" fill="url(#stemGrad_{uid})" />'
            f'<path d="M88 99 C95 84 94 66 86 55 C81 68 78 82 76 99 Z" fill="url(#stemGrad_{uid})" />'
            f'<path d="M58 100 C54 80 57 58 70 48 C83 58 86 80 82 100 Z" fill="url(#stemCenter_{uid})" />'
        )
        veins = (
            f'<path d="M62 92 Q42 64 31 38" stroke="#bbf7d0" stroke-width="1.6" fill="none" stroke-linecap="round" opacity="0.75"/>'
            f'<path d="M78 92 Q98 64 109 38" stroke="#bbf7d0" stroke-width="1.6" fill="none" stroke-linecap="round" opacity="0.75"/>'
            f'<path d="M66 90 Q53 56 51 27" stroke="#dcfce7" stroke-width="1.7" fill="none" stroke-linecap="round" opacity="0.85"/>'
            f'<path d="M74 90 Q87 56 89 27" stroke="#dcfce7" stroke-width="1.7" fill="none" stroke-linecap="round" opacity="0.85"/>'
            f'<path d="M70 88 L70 25" stroke="#f0fdf4" stroke-width="1.9" fill="none" stroke-linecap="round" opacity="0.9"/>'
        )
        badge_dot = f'<circle cx="112" cy="22" r="9" fill="#16a34a" stroke="#ffffff" stroke-width="2"/><path d="M108 22 L111 25 L116 19" stroke="#ffffff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    elif stage_key == "mendekati_panen" or m >= 66.5:
        outer_leaves = (
            f'<path d="M70 98 C38 86 22 60 30 38 C36 21 56 26 65 55 C68 67 69 83 70 98 Z" fill="url(#leafDark_{uid})" />'
            f'<path d="M70 98 C102 86 118 60 110 38 C104 21 84 26 75 55 C72 67 71 83 70 98 Z" fill="url(#leafDark_{uid})" />'
        )
        mid_leaves = (
            f'<path d="M70 98 C46 76 40 42 51 25 C60 12 71 26 70 56 C70 71 70 85 70 98 Z" fill="url(#leafMid_{uid})" />'
            f'<path d="M70 98 C94 76 100 42 89 25 C80 12 69 26 70 56 C70 71 70 85 70 98 Z" fill="url(#leafMid_{uid})" />'
            f'<path d="M70 97 C58 70 57 36 70 22 C83 36 82 70 70 97 Z" fill="url(#leafBright_{uid})" />'
        )
        petiole_bulb = (
            f'<path d="M56 99 C50 85 51 69 58 59 C62 71 64 84 65 99 Z" fill="url(#stemGrad_{uid})" />'
            f'<path d="M84 99 C90 85 89 69 82 59 C78 71 76 84 75 99 Z" fill="url(#stemGrad_{uid})" />'
            f'<path d="M61 100 C58 82 60 63 70 54 C80 63 82 82 79 100 Z" fill="url(#stemCenter_{uid})" />'
        )
        veins = (
            f'<path d="M63 92 Q45 66 36 42" stroke="#bbf7d0" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.75"/>'
            f'<path d="M77 92 Q95 66 104 42" stroke="#bbf7d0" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.75"/>'
            f'<path d="M67 90 Q56 58 54 31" stroke="#dcfce7" stroke-width="1.6" fill="none" stroke-linecap="round" opacity="0.85"/>'
            f'<path d="M73 90 Q84 58 86 31" stroke="#dcfce7" stroke-width="1.6" fill="none" stroke-linecap="round" opacity="0.85"/>'
            f'<path d="M70 89 L70 30" stroke="#f0fdf4" stroke-width="1.7" fill="none" stroke-linecap="round" opacity="0.9"/>'
        )
        badge_dot = ""
    else:
        outer_leaves = (
            f'<path d="M70 98 C45 86 32 64 38 45 C43 30 58 35 66 60 C68 70 69 84 70 98 Z" fill="url(#leafMid_{uid})" />'
            f'<path d="M70 98 C95 86 108 64 102 45 C97 30 82 35 74 60 C72 70 71 84 70 98 Z" fill="url(#leafMid_{uid})" />'
        )
        mid_leaves = (
            f'<path d="M70 98 C52 78 48 48 56 33 C63 22 71 34 70 60 C70 73 70 86 70 98 Z" fill="url(#leafBright_{uid})" />'
            f'<path d="M70 98 C88 78 92 48 84 33 C77 22 69 34 70 60 C70 73 70 86 70 98 Z" fill="url(#leafBright_{uid})" />'
            f'<path d="M70 97 C61 74 60 46 70 32 C80 46 79 74 70 97 Z" fill="#4ade80" opacity="0.85" />'
        )
        petiole_bulb = (
            f'<path d="M60 99 C56 86 57 73 62 65 C65 75 66 86 67 99 Z" fill="url(#stemGrad_{uid})" />'
            f'<path d="M80 99 C84 86 83 73 78 65 C75 75 74 86 73 99 Z" fill="url(#stemGrad_{uid})" />'
            f'<path d="M64 100 C62 85 63 70 70 62 C77 70 78 85 76 100 Z" fill="url(#stemCenter_{uid})" />'
        )
        veins = (
            f'<path d="M65 92 Q50 70 43 50" stroke="#dcfce7" stroke-width="1.4" fill="none" stroke-linecap="round" opacity="0.8"/>'
            f'<path d="M75 92 Q90 70 97 50" stroke="#dcfce7" stroke-width="1.4" fill="none" stroke-linecap="round" opacity="0.8"/>'
            f'<path d="M70 90 L70 39" stroke="#f0fdf4" stroke-width="1.6" fill="none" stroke-linecap="round" opacity="0.9"/>'
        )
        badge_dot = ""

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 130" width="{size}" height="{size}" style="overflow:visible;display:block;">'
        f'<defs>'
        f'<linearGradient id="leafDark_{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#16a34a"/><stop offset="100%" stop-color="#14532d"/>'
        f'</linearGradient>'
        f'<linearGradient id="leafMid_{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#22c55e"/><stop offset="100%" stop-color="#15803d"/>'
        f'</linearGradient>'
        f'<linearGradient id="leafBright_{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#4ade80"/><stop offset="100%" stop-color="#16a34a"/>'
        f'</linearGradient>'
        f'<linearGradient id="stemGrad_{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#bbf7d0"/><stop offset="45%" stop-color="#ecfdf5"/><stop offset="100%" stop-color="#d1fae5"/>'
        f'</linearGradient>'
        f'<linearGradient id="stemCenter_{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#dcfce7"/><stop offset="50%" stop-color="#ffffff"/><stop offset="100%" stop-color="#e2f8ec"/>'
        f'</linearGradient>'
        f'<linearGradient id="potGrad_{uid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="#3f624d"/><stop offset="100%" stop-color="#1e3528"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<ellipse cx="70" cy="119" rx="44" ry="6" fill="rgba(20,83,45,0.10)"/>'
        f'<g transform="translate(70, 99) scale({scale}) translate(-70, -99)">'
        f'{outer_leaves}'
        f'{mid_leaves}'
        f'{veins}'
        f'{petiole_bulb}'
        f'</g>'
        f'<ellipse cx="70" cy="99" rx="34" ry="5.5" fill="#422006"/>'
        f'<ellipse cx="70" cy="99" rx="29" ry="3.8" fill="#713f12" opacity="0.65"/>'
        f'<path d="M34 99 L106 99 L99 118 C98 121 94 123 89 123 L51 123 C46 123 42 121 41 118 Z" fill="url(#potGrad_{uid})"/>'
        f'<rect x="31" y="96" width="78" height="5.5" rx="2.7" fill="#2d4c39"/>'
        f'{badge_dot}'
        f'</svg>'
    )


_STAGE_IMG_CACHE = {}


def get_pakcoy_stage_img_b64(stage_key="masa_pertumbuhan", maturity_pct=50.0):
    """Mengembalikan data URL Base64 foto tanaman pakcoy asli yang sesuai dengan fase dan tingkat kematangan."""
    global _STAGE_IMG_CACHE
    m = float(maturity_pct)
    if stage_key == "siap_panen" or m >= 89.0:
        if m >= 95.0:
            file_name = "siap_panen_optimal.jpg"
        else:
            file_name = "siap_panen.jpg"
    elif stage_key == "mendekati_panen" or m >= 66.5:
        file_name = "mendekati_panen.jpg"
    elif m >= 55.0:
        file_name = "vegetatif_lanjut.jpg"
    elif m >= 35.0:
        file_name = "masa_pertumbuhan.jpg"
    else:
        file_name = "fase_awal.jpg"

    p = Path(__file__).parent / "assets" / "pakcoy_stages" / file_name
    if not p.exists():
        file_name = "masa_pertumbuhan.jpg"
        p = Path(__file__).parent / "assets" / "pakcoy_stages" / file_name

    if file_name not in _STAGE_IMG_CACHE and p.exists():
        _STAGE_IMG_CACHE[file_name] = f"data:image/jpeg;base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"
    return _STAGE_IMG_CACHE.get(file_name, "")


def _stage_style_from_maturity(mat_pct, thresholds):
    """Mengembalikan (stage_key, stage_label, text_color, bg_color, border_color, bar_color) dari persentase kematangan."""
    t1 = float(thresholds[0]) if thresholds and len(thresholds) >= 2 else 66.5
    t2 = float(thresholds[1]) if thresholds and len(thresholds) >= 2 else 89.0
    m = float(mat_pct)
    if m >= t2:
        return ("siap_panen", "Siap Panen", "#14532d", "#dcfce7", "#86efac", "#15803d")
    elif m >= t1:
        return ("mendekati_panen", "Mendekati Panen", "#854d0e", "#fef9c3", "#fde047", "#eab308")
    return ("masa_pertumbuhan", "Masa Pertumbuhan", "#0369a1", "#e0f2fe", "#7dd3fc", "#0284c7")


def _growth_desc_from_maturity(mat_pct):
    """Deskripsi singkat aktivitas pertumbuhan biologis berdasarkan persentase kematangan."""
    m = float(mat_pct)
    if m >= 89.0:
        return "Rimbun Padat · Siap Panen"
    elif m >= 66.5:
        return "Pelepah Tebal · Roset Lebat"
    elif m >= 55.0:
        return "Ekspansi Tajuk &amp; Roset Daun"
    elif m >= 35.0:
        return "Pertumbuhan Daun &amp; Batang Aktif"
    else:
        return "Fase Awal · Bibit &amp; Persemaian"


def forecast_4day_cards(table_df, start_day=None, thresholds=None, dry=55.0, wet=76.0, visual_mode="photo"):
    """Menampilkan 4 kartu visual prediksi 4 hari ke depan (Hari +1 s.d. Hari +4) lengkap dengan visualisasi tanaman Pakcoy."""
    if table_df is None or len(table_df) == 0:
        return

    mat_col = "Tingkat Kematangan (%)" if "Tingkat Kematangan (%)" in table_df.columns else "Maturity (%)"
    daily = (
        table_df.groupby("Hari", sort=False)
        .agg({"Kelembapan (%)": "mean", "Suhu (°C)": "mean", mat_col: "last", "Tahap": "last"})
        .round(1)
        .reset_index()
    )

    cards_html = []
    for idx, row in daily.iterrows():
        day_offset = idx + 1
        if start_day is not None and str(start_day).isdigit():
            actual_day = min(30, int(start_day) + day_offset)
            day_title = f"Hari ke-{actual_day}"
            if day_offset == 1:
                rel_badge = "Besok (+1 Hari)"
            elif day_offset == 2:
                rel_badge = "Lusa (+2 Hari)"
            elif day_offset == 3:
                rel_badge = "+3 Hari ke Depan"
            else:
                rel_badge = "+4 Hari ke Depan"
        else:
            actual_day = day_offset
            day_title = f"Hari ke-{actual_day}"
            rel_badge = f"+{day_offset} Hari"

        moist_v = float(row["Kelembapan (%)"])
        temp_v = float(row["Suhu (°C)"])
        mat_v = float(row[mat_col])
        st_key, st_lbl, st_col, st_bg, st_bdr, bar_col = _stage_style_from_maturity(mat_v, thresholds)
        morph = estimate_morphology_from_maturity(mat_v)

        if moist_v < dry:
            m_tag = "Perlu Siram"
            m_col = "#dc2626"
        elif moist_v >= wet:
            m_tag = "Terlalu Basah"
            m_col = "#0284c7"
        else:
            m_tag = "Ideal"
            m_col = "#15803d"

        # Skala pertumbuhan dinamis bertahap yang terlihat nyata (+9% per hari)
        img_scale = round(0.82 + (idx * 0.09) + (min(100.0, max(15.0, mat_v)) / 100.0) * 0.12, 2)
        if visual_mode == "svg":
            svg_plant = pakcoy_plant_svg(stage_key=st_key, maturity_pct=mat_v, uid=f"fc4_{idx}_{int(mat_v)}", size=118)
            plant_visual_html = f'<div class="fc-plant-svg-wrap">{svg_plant}</div>'
        else:
            img_src = get_pakcoy_stage_img_b64(st_key, mat_v)
            if img_src:
                plant_visual_html = (
                    f'<div class="fc-plant-img-wrap">'
                    f'<img src="{img_src}" alt="Foto Tanaman Pakcoy {_e(st_lbl)}" style="transform:scale({img_scale});" loading="lazy"/>'
                    f'</div>'
                )
            else:
                svg_plant = pakcoy_plant_svg(stage_key=st_key, maturity_pct=mat_v, uid=f"fc4_{idx}_{int(mat_v)}", size=118)
                plant_visual_html = f'<div class="fc-plant-svg-wrap">{svg_plant}</div>'

        bar_w = max(5, min(100, int(round(mat_v))))

        card = (
            f'<div class="fc-plant-card">'
            f'<div class="fc-plant-card-head">'
            f'<div class="fc-day-title-wrap">'
            f'<span class="fc-day-main">{_e(day_title)}</span>'
            f'<span class="fc-day-sub">{_e(rel_badge)}</span>'
            f'</div>'
            f'<span class="fc-stage-pill" style="color:{st_col};background:{st_bg};border:1px solid {st_bdr};">{_e(st_lbl)}</span>'
            f'</div>'
            f'<div class="fc-plant-visual">'
            f'{plant_visual_html}'
            f'<div class="fc-mat-row">'
            f'<div class="fc-mat-labels"><span>Tingkat Kematangan</span><span style="color:{st_col};font-weight:700;">{mat_v:.1f}%</span></div>'
            f'<div class="fc-mat-track"><div class="fc-mat-fill" style="width:{bar_w}%;background:{bar_col};"></div></div>'
            f'</div>'
            f'</div>'
            f'<div class="fc-growth-desc">{icon("sprout", 12, color=st_col)} {_growth_desc_from_maturity(mat_v)}</div>'
            f'<div class="fc-metrics-list">'
            f'<div class="fc-metric-box">'
            f'<div class="fc-metric-lbl">{icon("droplets", 12, color="#0284c7")}<span>Kelembapan</span></div>'
            f'<div class="fc-metric-val">{moist_v:.1f}% <span style="font-size:10.5px;color:{m_col};font-weight:600;">({m_tag})</span></div>'
            f'</div>'
            f'<div class="fc-metric-box">'
            f'<div class="fc-metric-lbl">{icon("thermometer", 12, color="#ea580c")}<span>Suhu Udara</span></div>'
            f'<div class="fc-metric-val">{temp_v:.1f}°C</div>'
            f'</div>'
            f'</div>'
            f'<div class="fc-morph-footer">'
            f'<span>{icon("sprout", 13, color="#15803d")} Est. Daun: <strong>±{morph["leaf_len_cm"]} cm</strong></span>'
            f'<span>Tajuk: <strong>±{morph["canopy_dia_cm"]} cm</strong></span>'
            f'</div>'
            f'</div>'
        )
        cards_html.append(card)

    info_html = ""
    if start_day is not None and str(start_day).isdigit():
        s_d = int(start_day)
        e_d = min(30, s_d + 4)
        info_html = (
            f'<div class="fc-info-note">'
            f'{icon("info", 15, color="#15803d")}'
            f'<div><strong>Titik Pantau Saat Ini: Hari ke-{s_d}.</strong> '
            f'Kartu di bawah memprakirakan kondisi tanaman dari <strong>Besok (Hari ke-{s_d+1})</strong> '
            f'hingga <strong>Hari ke-{e_d} (+4 Hari)</strong>. '
            f'<span style="color:#2c5a3e;">(Siklus tanam pakcoy adalah 30 hari. Umur 8–20 hari masih tergolong fase Masa Pertumbuhan vegetatif aktif. '
            f'Gunakan tombol <em>"Menjelang Panen · Hari ke-25"</em> di atas untuk melihat peralihan fase ke Mendekati Panen &amp; Siap Panen).</span>'
            f'</div>'
            f'</div>'
        )

    st.markdown(f'{info_html}<div class="fc-plant-grid">{"".join(cards_html)}</div>', unsafe_allow_html=True)


def lstm_stage_visual_card(stage_key, stage_label, confidence, truth_label, moist, temp, day_val, time_val, mat_pct=55.0):
    """Menampilkan kartu visual tanaman Pakcoy untuk hasil deteksi fase LSTM saat ini."""
    morph = estimate_morphology_from_maturity(mat_pct)
    img_src = get_pakcoy_stage_img_b64(stage_key, mat_pct)
    if img_src:
        plant_visual_html = f'<div class="lstm-plant-img-wrap"><img src="{img_src}" alt="Foto Tanaman Pakcoy {_e(stage_label)}" /></div>'
    else:
        svg_plant = pakcoy_plant_svg(stage_key=stage_key, maturity_pct=mat_pct, uid=f"lstm_cur_{int(mat_pct)}", size=140)
        plant_visual_html = svg_plant

    if stage_key == "siap_panen":
        st_col, st_bg, st_bdr = "#14532d", "#dcfce7", "#86efac"
    elif stage_key == "mendekati_panen":
        st_col, st_bg, st_bdr = "#854d0e", "#fef9c3", "#fde047"
    else:
        st_col, st_bg, st_bdr = "#0369a1", "#e0f2fe", "#7dd3fc"

    day_str = f"Hari ke-{day_val} · {time_val}" if str(day_val) != "?" else "Simulasi Manual Sensor"
    html_out = (
        f'<div class="lstm-visual-hero">'
        f'<div class="lstm-visual-left">'
        f'{plant_visual_html}'
        f'<span class="fc-stage-pill" style="margin-top:8px;color:{st_col};background:{st_bg};border:1px solid {st_bdr};">'
        f'Foto Asli · {_e(stage_label)}'
        f'</span>'
        f'</div>'
        f'<div class="lstm-visual-right">'
        f'<div class="lstm-visual-head">'
        f'<div>'
        f'<div style="font-size:11.5px;font-weight:700;color:#15803d;text-transform:uppercase;letter-spacing:0.04em;">Hasil Prediksi Fase Tanaman (AI LSTM)</div>'
        f'<div class="lstm-visual-stage">{_e(stage_label)}</div>'
        f'</div>'
        f'<div class="lstm-visual-badges">'
        f'<span class="fc-day-badge">Keyakinan AI: {confidence:.0%}</span>'
        f'<span class="fc-day-badge" style="background:#f8fbf9;color:#2c3e35;border-color:#d5e2d9;">{_e(day_str)}</span>'
        f'</div>'
        f'</div>'
        f'<div class="lstm-visual-stats">'
        f'<div class="lstm-stat-item"><div class="lstm-stat-lbl">Kelembapan Tanah</div><div class="lstm-stat-val">{moist:.1f}%</div></div>'
        f'<div class="lstm-stat-item"><div class="lstm-stat-lbl">Suhu Udara</div><div class="lstm-stat-val">{temp:.1f}°C</div></div>'
        f'<div class="lstm-stat-item"><div class="lstm-stat-lbl">Est. Panjang &amp; Lebar Daun</div><div class="lstm-stat-val">±{morph["leaf_len_cm"]} × {morph["leaf_wid_cm"]} cm</div></div>'
        f'<div class="lstm-stat-item"><div class="lstm-stat-lbl">Catatan Kebun (Pembanding)</div><div class="lstm-stat-val">{_e(truth_label)}</div></div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html_out, unsafe_allow_html=True)





