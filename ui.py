"""Komponen tampilan profesional (CSS, kartu KPI, banner, SVG icons) untuk Smart Farming Pakcoy.
Sistem desain berdasarkan DESIGN.md (Light Theme, Inter font, pill button, bento cards)."""
import html
import re
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
    r"✅❌⚠️⚠▶⏸✓🔥💧🌡🌱📈🤖🗓📄🔍📉⚡🎯🧺🌿🧱📐🍃🎨↔📏🔮🖼🏠📊📡🧠📅📸⬇]+",
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
    "sparkles": '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "maximize": '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>',
    "sliders": '<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/>',
    "camera": '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
    "message-square": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
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


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
  --primary: #533afd;
  --primary-deep: #4434d4;
  --primary-press: #2e2b8c;
  --primary-soft: #665efd;
  --primary-subdued: #eeedfe;
  --primary-bg-subdued-hover: #b9b9f9;
  --brand-dark-900: #1c1e54;
  --ink: #0d253d;
  --ink-secondary: #273951;
  --ink-mute: #64748d;
  --ink-mute-2: #61718a;
  --on-primary: #ffffff;
  --canvas: #ffffff;
  --canvas-soft: #f6f9fc;
  --canvas-cream: #f5e9d4;
  --hairline: #e3e8ee;
  --hairline-input: #a8c3de;
  --ruby: #ea2261;
  --magenta: #f96bee;
  --lemon: #9b6829;
  --shadow-blue: #003770;
  --success: #00875a;
  --success-bg: rgba(0, 135, 90, 0.08);
  --warning: #fb923c;
  --warning-bg: rgba(251, 146, 60, 0.10);
  --danger: #ea2261;
  --danger-bg: rgba(234, 34, 97, 0.08);
  --info: #533afd;
  --info-bg: rgba(83, 58, 253, 0.07);
  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-pill: 9999px;
}

/* Global App Styling */
html, body, [class*="css"], .stApp {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  font-feature-settings: "ss01" !important;
  color: var(--ink);
  background-color: var(--canvas-soft);
}

.block-container {
  padding-top: 1.8rem;
  padding-bottom: 2.5rem;
  max-width: 1280px;
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

/* Sidebar Toggle / Reopen Button */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
  display: flex !important;
  visibility: visible !important;
  color: var(--primary) !important;
  background-color: var(--canvas) !important;
  border: 1px solid var(--hairline) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: rgba(0, 55, 112, 0.08) 0 2px 8px !important;
  margin: 8px !important;
  z-index: 999999 !important;
}

/* Sidebar Container: lebar kembali ke sekitar 280-300px (290px) */
section[data-testid="stSidebar"],
[data-testid="stSidebar"] {
  background-color: var(--canvas) !important;
  border-right: 1px solid var(--hairline) !important;
  width: 290px !important;
  min-width: 280px !important;
  max-width: 300px !important;
}

/* Typography: Apply Inter selectively (DO NOT use universal * which breaks Material Symbols icons) */
[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] span:not([data-testid="stIconMaterial"]):not([class*="material"]):not([class*="Icon"]),
[data-testid="stSidebar"] div:not([data-testid="stIconMaterial"]):not([class*="material"]) {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
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

/* Tombol buka-tutup sidebar di dalam header sidebar */
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
  height: auto !important;
  min-height: 28px !important;
  padding: 6px 12px 0 12px !important;
  margin: 0 !important;
  display: flex !important;
  justify-content: flex-end !important;
  align-items: center !important;
  background: transparent !important;
  position: static !important;
}

[data-testid="stSidebar"] button[aria-label="Collapse sidebar"],
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
  display: flex !important;
  visibility: visible !important;
  color: var(--ink-mute) !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  cursor: pointer !important;
  padding: 4px !important;
  margin: 0 !important;
}

[data-testid="stSidebar"] button[aria-label="Collapse sidebar"]:hover,
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover {
  color: var(--primary) !important;
}

/* Sidebar Scroll & Content Container: padding horizontal 16px, padding atas 8px */
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  padding: 0 !important;
  background-color: var(--canvas) !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
[data-testid="stSidebarUserContent"] {
  padding-top: 8px !important;
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

/* Brand Section: SATU baris, gap 10px, kotak ikon 36px, sub 13.5px jarak 6px */
.brand {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  font-size: 20px !important;
  font-weight: 600 !important;
  color: #0d253d !important;
  margin: 0 !important;
  padding: 0 !important;
  letter-spacing: -0.02em !important;
  line-height: 1.25 !important;
  white-space: nowrap !important;
}

.brand span:last-child {
  font-size: 20px !important;
  font-weight: 600 !important;
  letter-spacing: -0.02em !important;
  white-space: nowrap !important;
  color: #0d253d !important;
}

.brand-icon-box {
  width: 36px !important;
  height: 36px !important;
  min-width: 36px !important;
  min-height: 36px !important;
  border-radius: 8px !important;
  background-color: var(--primary-subdued) !important;
  color: var(--primary) !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
}

.brand-sub {
  color: #64748d !important;
  font-size: 13.5px !important;
  margin-top: 6px !important;
  margin-bottom: 0 !important;
  padding: 0 !important;
  line-height: 1.45 !important;
  display: block !important;
}

/* Section Headings (20px top space, 8px bottom space to its content) */
.micro-cap {
  display: block !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  color: #64748d !important;
  line-height: 14px !important;
  padding-top: 20px !important;
  padding-bottom: 8px !important;
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

/* Sidebar Radio Group */
[data-testid="stSidebar"] [data-testid="stRadio"] {
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioGroup"],
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
  display: flex !important;
  flex-direction: column !important;
  gap: 2px !important;
  margin: 0 !important;
  padding: 1px 0 !important;
  overflow: visible !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] .react-aria-RadioField {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
}

/* Sidebar Radio Option - Item Biasa (SaaS clean style) */
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioOption"],
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label {
  display: flex !important;
  width: 100% !important;
  box-sizing: border-box !important;
  align-items: center !important;
  gap: 10px !important;
  padding: 0 12px !important;
  border-radius: 8px !important;
  min-height: 36px !important;
  height: 36px !important;
  color: #273951 !important;
  font-size: 14px !important;
  font-weight: 400 !important;
  cursor: pointer !important;
  transition: background-color 0.15s ease, color 0.15s ease !important;
  background-color: transparent !important;
  border: none !important;
  border-left: none !important;
  margin: 0 !important;
  outline: none !important;
  box-shadow: none !important;
  overflow: visible !important;
}

/* Remove default p tag margin */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label p,
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioOption"] p {
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1.2 !important;
  font-size: 14px !important;
  color: inherit !important;
  font-weight: inherit !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* Inner flex wrapper */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label > div {
  display: flex !important;
  align-items: center !important;
  flex: 1 !important;
  min-width: 0 !important;
}

/* Remove focus stickiness */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:focus,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:focus-visible,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-focus-visible] {
  outline: none !important;
  box-shadow: none !important;
  background-color: transparent !important;
}

/* Hover inactive item: hover latar #f6f9fc saja */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover {
  background-color: #f6f9fc !important;
  color: #273951 !important;
}

/* Active item: 1 penanda latar #eeedfe (radius 8px), teks indigo #533afd weight 500, tanpa garis kiri */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked),
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-selected="true"],
[data-testid="stSidebar"] [data-testid="stRadio"] .react-aria-RadioField[data-selected="true"] label {
  background-color: #eeedfe !important;
  color: #533afd !important;
  font-weight: 500 !important;
  border: none !important;
  border-left: none !important;
  border-radius: 8px !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked):hover,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-selected="true"]:hover {
  background-color: #eeedfe !important;
  color: #533afd !important;
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

/* Nav Item SVG Icons via CSS Mask: ikon abu redup #64748d */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label::before {
  content: "" !important;
  display: inline-block !important;
  width: 18px !important;
  height: 18px !important;
  min-width: 18px !important;
  max-width: 18px !important;
  background-color: #64748d !important;
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
  background-color: #273951 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked)::before,
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-selected="true"]::before,
[data-testid="stSidebar"] [data-testid="stRadio"] .react-aria-RadioField[data-selected="true"] label::before {
  background-color: #533afd !important;
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

/* ================================================================= AI Assistant Framed Card Interface */
.st-key-chat_main_card {
  max-width: 920px !important;
  margin: 0 auto 0 auto !important;
  background-color: #ffffff !important;
  border: 1px solid #e3e8ee !important;
  border-radius: 16px !important;
  box-shadow: rgba(0, 55, 112, 0.08) 0 8px 24px !important;
  overflow: visible !important;
  box-sizing: border-box !important;
}

.st-key-chat_main_card > div {
  padding: 0 !important;
  gap: 0 !important;
}

/* 1. Header Bingkai (Tinggi ~64px, padding 12px 20px, border-bottom #e3e8ee, rounded top) */
.st-key-chat_header_row {
  min-height: 64px !important;
  padding: 12px 20px !important;
  border-bottom: 1px solid #e3e8ee !important;
  background-color: #ffffff !important;
  border-top-left-radius: 15px !important;
  border-top-right-radius: 15px !important;
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
  background-color: #eeedfe !important;
  color: #533afd !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
}

.chat-header-title {
  font-size: 15px !important;
  font-weight: 600 !important;
  color: #0d253d !important;
  line-height: 1.25 !important;
}

.chat-header-sub {
  font-size: 12.5px !important;
  color: #64748d !important;
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
  background-color: #f6f9fc !important;
}

.st-key-btn_clear_chat button::after {
  content: "" !important;
  display: block !important;
  width: 18px !important;
  height: 18px !important;
  background-color: #64748d !important;
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
  background-color: #ea2261 !important;
}

/* 2. Area Pesan (Internal scroll, adaptif terhadap layar 934px agar bingkai utuh) */
.st-key-chat_scroll_area {
  height: calc(100vh - 400px) !important;
  min-height: 300px !important;
  max-height: 460px !important;
  background-color: #fbfcfe !important;
  border: none !important;
  border-top: none !important;
  border-bottom: none !important;
  padding: 16px 20px !important;
  overflow-y: auto !important;
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
  border-radius: 12px !important;
  background-color: #eeedfe !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  margin-bottom: 12px !important;
}

.chat-empty-title {
  font-size: 16px !important;
  font-weight: 600 !important;
  color: #0d253d !important;
  margin-bottom: 4px !important;
}

.chat-empty-sub {
  font-size: 13px !important;
  color: #64748d !important;
  max-width: 460px !important;
  line-height: 1.45 !important;
  margin-bottom: 16px !important;
}

/* 4 Saran Pertanyaan sebagai grid 2x2 kartu kecil: teks rata kiri (bukan tengah), padding 12px 14px, tinggi seragam */
[class*="st-key-sug_card_"] button,
[class*="st-key-sug_card_"] [data-testid="stBaseButton-secondary"],
.st-key-chat_main_card .st-key-chat_scroll_area [data-testid="stBaseButton-secondary"],
.st-key-chat_main_card .st-key-chat_scroll_area .stButton > button,
.st-key-chat_main_card .st-key-chat_scroll_area .stButton > button[kind="secondary"] {
  background-color: #ffffff !important;
  border: 1px solid #e3e8ee !important;
  border-radius: 10px !important;
  color: #273951 !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  line-height: 1.45 !important;
  padding: 12px 14px !important;
  text-align: left !important;
  justify-content: flex-start !important;
  align-items: center !important;
  box-shadow: rgba(0, 55, 112, 0.02) 0 1px 3px !important;
  transition: all 0.15s ease !important;
  min-height: 56px !important;
  height: 56px !important;
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
  background-color: #f6f9fc !important;
  border-color: #533afd !important;
  color: #533afd !important;
  box-shadow: rgba(83, 58, 253, 0.08) 0 2px 6px !important;
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
/* Row alignment right */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
[data-testid="stChatMessage"]:has([data-testid*="User"]),
[data-testid="stChatMessage"]:has([aria-label*="user"]) {
  flex-direction: row-reverse !important;
  justify-content: flex-start !important;
}

/* Hide user avatar */
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessage"] [data-testid*="AvatarUser"],
[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid*="Avatar"] {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* User Bubble: Balon indigo #533afd, padding 12px 16px, radius 16px 16px 4px 16px, max 75% */
[data-testid="stChatMessageContent"][aria-label*="user"],
[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stChatMessageContent"] {
  background-color: #533afd !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 16px 16px 4px 16px !important;
  padding: 12px 16px !important;
  box-shadow: rgba(83, 58, 253, 0.15) 0 2px 6px !important;
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

[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stChatMessageContent"] p,
[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stChatMessageContent"] span {
  color: #ffffff !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
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
/* Row alignment left with avatar */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]),
[data-testid="stChatMessage"]:has([data-testid*="Assistant"]),
[data-testid="stChatMessage"]:has([aria-label*="assistant"]),
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) {
  flex-direction: row !important;
  justify-content: flex-start !important;
  gap: 10px !important;
}

/* Assistant Avatar: Kotak 28px #eeedfe dengan ikon sprout SVG indigo */
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
  background-color: #eeedfe !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
  margin-top: 2px !important;
  border: none !important;
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
  background-color: #533afd !important;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7 20h10'/%3E%3Cpath d='M10 20c5.5-2.5.8-6.4 3-10'/%3E%3Cpath d='M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4.1 5.5.8z'/%3E%3Cpath d='M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7 20h10'/%3E%3Cpath d='M10 20c5.5-2.5.8-6.4 3-10'/%3E%3Cpath d='M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4.1 5.5.8z'/%3E%3Cpath d='M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z'/%3E%3C/svg%3E") !important;
  -webkit-mask-size: contain !important;
  mask-size: contain !important;
  -webkit-mask-repeat: no-repeat !important;
  mask-repeat: no-repeat !important;
  -webkit-mask-position: center !important;
  mask-position: center !important;
}

/* Assistant Bubble: Putih, border #e3e8ee, radius 16px 16px 16px 4px, padding 12px 16px, max 85%, rata kiri */
[data-testid="stChatMessageContent"][aria-label*="assistant"],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"],
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] {
  background-color: #ffffff !important;
  color: #0d253d !important;
  border: 1px solid #e3e8ee !important;
  border-radius: 16px 16px 16px 4px !important;
  padding: 12px 16px !important;
  box-shadow: rgba(0, 55, 112, 0.04) 0 1px 3px !important;
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

/* Seragamkan ukuran teks Markdown asisten: p, li, li p, ul, ol, strong, em font-size 14px, line-height 1.6, #0d253d */
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] p,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] li,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] ul,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] ol,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] strong,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] em,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stChatMessageContent"] span {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  color: #0d253d !important;
}

[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] li p {
  margin: 0 !important;
  padding: 0 !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  color: #0d253d !important;
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
  color: #0d253d !important;
}

[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] li:last-child {
  margin-bottom: 0 !important;
}

/* Penanda sub-butir kecil (lingkaran) */
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] ul ul,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] ol ul {
  list-style-type: circle !important;
  margin-top: 4px !important;
  margin-bottom: 4px !important;
  padding-left: 18px !important;
}

/* Judul markdown h1-h4 di dalam balon dibatasi 15px weight 600 */
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] h1,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] h2,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] h3,
[data-testid="stChatMessage"]:not(:has([data-testid*="User"])) [data-testid="stMarkdownContainer"] h4 {
  font-size: 15px !important;
  font-weight: 600 !important;
  color: #0d253d !important;
  margin-top: 8px !important;
  margin-bottom: 6px !important;
  line-height: 1.4 !important;
}

/* Code block di dalam chat */
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] pre,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
  background-color: #f6f9fc !important;
  border: 1px solid #e3e8ee !important;
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
  background-color: #533afd !important;
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
  background-color: #fff5f7 !important;
  border-left: 3px solid #ea2261 !important;
  color: #0d253d !important;
  font-size: 13px !important;
  padding: 10px 14px !important;
  border-radius: 0 8px 8px 0 !important;
  margin: 8px 0 !important;
  line-height: 1.45 !important;
}

/* 3. Area Input (di dalam bingkai, padding atas 14px, samping 20px, bawah 16px) */
.st-key-chat_input_section {
  border-top: 1px solid #e3e8ee !important;
  padding: 14px 20px 16px 20px !important;
  background-color: #ffffff !important;
  border-bottom-left-radius: 15px !important;
  border-bottom-right-radius: 15px !important;
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

/* Kolom input: Satu border saja, 1px #a8c3de, radius 12px */
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
  border-radius: 12px !important;
  border: 1px solid #a8c3de !important;
  background-color: #ffffff !important;
  box-shadow: none !important;
  outline: none !important;
  padding: 4px 6px 4px 12px !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
  display: flex !important;
  align-items: center !important;
}

/* Fokus hanya ditandai pada kolom input (border #533afd + ring 3px rgba(83,58,253,0.12)) */
.st-key-chat_input_section [data-testid="stChatInput"] > div:focus-within {
  border-color: #533afd !important;
  box-shadow: 0 0 0 3px rgba(83, 58, 253, 0.12) !important;
  outline: none !important;
}

.st-key-chat_input_section [data-testid="stChatInput"] textarea,
.st-key-chat_input_section [data-testid="stChatInputTextArea"] {
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  color: #0d253d !important;
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

/* Hilangkan border/outline/box-shadow pada wrapper pembungkus tombol kirim */
.st-key-chat_input_section [data-testid="stChatInput"] div:has(> [data-testid="stChatInputSubmitButton"]),
.st-key-chat_input_section [data-testid="stChatInput"] div.st-emotion-cache-k1jj38 {
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  background: transparent !important;
  padding: 0 !important;
  margin: 0 !important;
}

/* Tombol kirim: 32x32px, radius 8px, tanpa border */
[data-testid="stChatInputSubmitButton"],
.st-key-chat_input_section [data-testid="stChatInputSubmitButton"],
.st-key-chat_input_section button[aria-label="Send message"],
.st-key-chat_input_section [data-testid="stChatInput"] button {
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  border-radius: 8px !important;
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
  background-color: #533afd !important;
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

/* Aktif (ada teks): latar #533afd, ikon putih, hover #4434d4 */
.st-key-chat_input_section [data-testid="stChatInputSubmitButton"]:hover:not(:disabled),
.st-key-chat_input_section [data-testid="stChatInput"] button:hover:not(:disabled) {
  background-color: #4434d4 !important;
  color: #ffffff !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}

/* Disabled (input kosong): latar transparan, ikon #a8c3de, tanpa kotak */
.st-key-chat_input_section [data-testid="stChatInputSubmitButton"]:disabled,
.st-key-chat_input_section [data-testid="stChatInput"] button:disabled {
  background: transparent !important;
  background-color: transparent !important;
  color: #a8c3de !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  cursor: default !important;
}

.st-key-chat_input_section [data-testid="stChatInputSubmitButton"]:disabled svg,
.st-key-chat_input_section [data-testid="stChatInput"] button:disabled svg {
  fill: #a8c3de !important;
  stroke: #a8c3de !important;
  color: #a8c3de !important;
  border: none !important;
  outline: none !important;
}

/* Hilangkan ring fokus ganda; fokus cukup pada input */
.st-key-chat_input_section [data-testid="stChatInputSubmitButton"]:focus,
.st-key-chat_input_section [data-testid="stChatInputSubmitButton"]:focus-visible,
.st-key-chat_input_section [data-testid="stChatInput"] button:focus,
.st-key-chat_input_section [data-testid="stChatInput"] button:focus-visible {
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}

/* Catatan kaki di dalam bingkai: 11px #64748d, jarak 10px di bawah input (lewat gap), line-height 1.4, rata tengah */
.chat-frame-footer-note {
  font-size: 11px !important;
  color: #64748d !important;
  text-align: center !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1.4 !important;
  display: block !important;
  width: 100% !important;
}

/* Responsive */
@media (max-width: 768px) {
  .st-key-chat_main_card {
    margin: 0 12px 16px 12px !important;
    max-width: calc(100% - 24px) !important;
  }
  .st-key-chat_scroll_area {
    height: 420px !important;
    max-height: 420px !important;
    padding: 14px 12px !important;
  }
}

/* Sidebar Uploader (DATA) */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
  margin: 0 !important;
  padding: 0 !important;
  display: block !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] > label,
[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stFileUploader"] label p {
  font-size: 13px !important;
  font-weight: 400 !important;
  color: #273951 !important;
  margin: 0 0 8px 0 !important;
  padding: 0 !important;
  line-height: 1.3 !important;
  display: block !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] section,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
  padding: 12px !important;
  background-color: #ffffff !important;
  border: 1px dashed #a8c3de !important;
  border-radius: 8px !important;
  min-height: auto !important;
  margin: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] section small,
[data-testid="stSidebar"] [data-testid="stFileUploaderInstructions"],
[data-testid="stSidebar"] [data-testid="stFileUploaderInstructions"] small,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {
  font-size: 11.5px !important;
  color: #64748d !important;
  line-height: 1.3 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
  height: 32px !important;
  min-height: 32px !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  background-color: #ffffff !important;
  color: #273951 !important;
  border: 1px solid #e3e8ee !important;
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
  background-color: #f6f9fc !important;
  border-color: #a8c3de !important;
  color: #273951 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button [data-testid="stIconMaterial"],
[data-testid="stSidebar"] [data-testid="stFileUploader"] button span[class*="material"] {
  color: #64748d !important;
  font-size: 16px !important;
  margin-right: 2px !important;
}

/* Sidebar Button - "Muat ulang model" (Aksi Sekunder SaaS) */
[data-testid="stSidebar"] .stButton {
  margin: 12px 0 0 0 !important;
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
  height: 36px !important;
  min-height: 36px !important;
  border-radius: 8px !important;
  background-color: #ffffff !important;
  color: #273951 !important;
  border: 1px solid #e3e8ee !important;
  font-size: 13px !important;
  font-weight: 500 !important;
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
  background-color: #f6f9fc !important;
  border-color: #a8c3de !important;
  color: #273951 !important;
}

/* Sidebar Divider */
[data-testid="stSidebar"] hr,
[data-testid="stSidebar"] [data-testid="stDivider"] {
  border: none !important;
  border-top: 1px solid #e3e8ee !important;
  height: 1px !important;
  margin-top: 24px !important;
  margin-bottom: 12px !important;
  padding: 0 !important;
  display: block !important;
  clear: both !important;
}

/* Sidebar Footer Caption */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] .stCaption {
  margin: 0 !important;
  padding: 0 !important;
  display: block !important;
  clear: both !important;
}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] .stCaption p {
  font-size: 11px !important;
  color: #64748d !important;
  line-height: 1.4 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* Button SVG icons */
.st-key-reload_models button::before {
  content: "" !important;
  display: inline-block !important;
  width: 14px !important;
  height: 14px !important;
  margin-right: 7px !important;
  background-color: #64748d !important;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8'/%3E%3Cpath d='M21 3v5h-5'/%3E%3Cpath d='M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16'/%3E%3Cpath d='M3 21v-5h5'/%3E%3C/svg%3E") no-repeat center / contain !important;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8'/%3E%3Cpath d='M21 3v5h-5'/%3E%3Cpath d='M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16'/%3E%3Cpath d='M3 21v-5h5'/%3E%3C/svg%3E") no-repeat center / contain !important;
  flex-shrink: 0 !important;
  transition: background-color 0.15s ease !important;
}

.st-key-reload_models button:hover::before {
  background-color: #273951 !important;
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

/* Hero Banner with Soft Gradient Mesh */
.hero {
  position: relative;
  background: 
    radial-gradient(circle at 10% 20%, rgba(245, 233, 212, 0.90) 0%, transparent 45%),
    radial-gradient(circle at 88% 15%, rgba(249, 107, 238, 0.35) 0%, transparent 45%),
    radial-gradient(circle at 50% 85%, rgba(185, 185, 249, 0.55) 0%, transparent 50%),
    radial-gradient(circle at 20% 90%, rgba(251, 146, 60, 0.30) 0%, transparent 40%),
    radial-gradient(circle at 75% 85%, rgba(83, 58, 253, 0.20) 0%, transparent 50%),
    #ffffff;
  border: 1px solid var(--hairline);
  border-radius: var(--radius-lg);
  padding: 24px 28px;
  margin-bottom: 18px;
  box-shadow: rgba(0, 55, 112, 0.05) 0 2px 8px;
}

.hero-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.hero-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(83, 58, 253, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hero h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 300;
  letter-spacing: -0.5px;
  line-height: 1.2;
  color: var(--ink);
}

.hero p {
  margin: 0;
  color: var(--ink-secondary);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
}

/* Bento KPI Cards */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin: 10px 0 18px;
}

.kpi {
  background: var(--canvas);
  border: 1px solid var(--hairline);
  border-radius: var(--radius-lg);
  padding: 16px 14px;
  box-shadow: rgba(0, 55, 112, 0.05) 0 1px 3px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  min-height: 100px;
}

.kpi:hover {
  transform: translateY(-2px);
  box-shadow: rgba(0, 55, 112, 0.08) 0 4px 12px;
}

.kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.kpi-label {
  color: var(--ink-mute);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.kpi-icon-pill {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-value {
  font-size: 24px;
  font-weight: 600;
  font-feature-settings: "tnum";
  line-height: 1.15;
  letter-spacing: -0.3px;
}

.kpi-sub {
  color: var(--ink-mute);
  font-size: 11.5px;
  font-weight: 400;
  margin-top: 3px;
}

/* Banners */
.banner {
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin: 10px 0;
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
  background: var(--success-bg);
  border-color: var(--success);
  color: var(--ink);
}

.banner.ok .banner-icon { color: var(--success); }

.banner.warn {
  background: var(--warning-bg);
  border-color: var(--warning);
  color: var(--ink);
}

.banner.warn .banner-icon { color: var(--warning); }

.banner.danger {
  background: var(--danger-bg);
  border-color: var(--danger);
  color: var(--ink);
}

.banner.danger .banner-icon { color: var(--danger); }

.banner.info {
  background: var(--info-bg);
  border-color: var(--primary);
  color: var(--ink);
}

.banner.info .banner-icon { color: var(--primary); }

/* LIVE Badge */
.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(234, 34, 97, 0.08);
  color: var(--ruby);
  border: 1px solid rgba(234, 34, 97, 0.25);
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.live-badge.paused {
  background: rgba(100, 116, 139, 0.08);
  color: var(--ink-mute);
  border-color: var(--hairline);
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ruby);
  animation: pulse 1.4s infinite;
}

.paused .live-dot {
  background: var(--ink-mute);
  animation: none;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(234, 34, 97, 0.5); }
  70% { box-shadow: 0 0 0 7px rgba(234, 34, 97, 0); }
  100% { box-shadow: 0 0 0 0 rgba(234, 34, 97, 0); }
}

/* Section Title */
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--ink);
  margin: 16px 0 8px 0;
  letter-spacing: -0.2px;
}

.section-icon {
  display: inline-flex;
  align-items: center;
  color: var(--ink-mute);
}

/* Streamlit Native Components Light Overrides */
.stButton > button[kind="primary"] {
  background-color: var(--primary) !important;
  color: #ffffff !important;
  border-radius: var(--radius-pill) !important;
  border: none !important;
  font-weight: 500 !important;
  padding: 8px 18px !important;
  box-shadow: rgba(83, 58, 253, 0.2) 0 2px 6px !important;
  font-size: 14px !important;
}

.stButton > button[kind="primary"]:hover {
  background-color: var(--primary-deep) !important;
  color: #ffffff !important;
}

/* Streamlit Native Components Light Overrides - Main area secondary buttons only */
.main .stButton > button[kind="secondary"],
[data-testid="stMainBlockContainer"] div:not([class*="sug_card_"]):not(.st-key-chat_header_row) > .stButton > button[kind="secondary"] {
  background-color: var(--canvas) !important;
  color: var(--primary) !important;
  border: 1px solid var(--primary) !important;
  border-radius: var(--radius-pill) !important;
  font-weight: 500 !important;
  padding: 8px 18px !important;
  font-size: 14px !important;
}

.stDownloadButton > button {
  background-color: var(--canvas) !important;
  color: var(--primary) !important;
  border: 1px solid var(--primary) !important;
  border-radius: var(--radius-pill) !important;
  font-weight: 500 !important;
  padding: 8px 18px !important;
  font-size: 14px !important;
  transition: all 0.15s ease !important;
}

.stDownloadButton > button:hover {
  background-color: rgba(83, 58, 253, 0.06) !important;
  border-color: var(--primary-deep) !important;
}

/* Input Fields */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  border-radius: var(--radius-sm) !important;
  border-color: var(--hairline-input) !important;
  background-color: var(--canvas) !important;
  color: var(--ink) !important;
}

[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
  border-radius: var(--radius-sm) !important;
  border-color: var(--hairline-input) !important;
  background-color: var(--canvas) !important;
  color: var(--ink) !important;
}

/* Expanders */
[data-testid="stExpander"] {
  background: var(--canvas) !important;
  border: 1px solid var(--hairline) !important;
  border-radius: var(--radius-lg) !important;
  box-shadow: rgba(0, 55, 112, 0.03) 0 1px 3px !important;
  overflow: hidden !important;
}

[data-testid="stExpander"] summary {
  font-weight: 600 !important;
  color: var(--ink) !important;
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 6px !important;
  border-bottom: 1px solid var(--hairline) !important;
  background: transparent !important;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  color: var(--ink-mute) !important;
  font-weight: 500 !important;
  padding: 8px 16px !important;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
  background: transparent !important;
  border: none !important;
}

[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
  color: var(--primary) !important;
  font-weight: 600 !important;
  border-bottom: 2px solid var(--primary) !important;
}

/* Dataframe */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
  border: 1px solid var(--hairline) !important;
  border-radius: var(--radius-md) !important;
  background: var(--canvas) !important;
  box-shadow: rgba(0, 55, 112, 0.03) 0 1px 2px !important;
}

/* Dividers */
hr {
  margin: 1.2rem 0 !important;
  border-color: var(--hairline) !important;
}

/* Footer: jarak antara bingkai chat / konten ke garis footer sekitar 24px */
.footer {
  color: var(--ink-mute);
  font-size: 0.78rem;
  text-align: center;
  margin-top: 8px !important;
  padding-top: 14px;
  border-top: 1px solid var(--hairline);
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def _e(x):
    return html.escape(str(x))


def hero(title, subtitle, icon_name="sprout"):
    clean_title = strip_emoji(title)
    icon_svg = icon(icon_name, 22, color="var(--primary)")
    st.markdown(
        f'<div class="hero">'
        f'<div class="hero-header">'
        f'<div class="hero-icon-box">{icon_svg}</div>'
        f'<h1>{_e(clean_title)}</h1>'
        f'</div>'
        f'<p>{_e(subtitle)}</p>'
        f'</div>',
        unsafe_allow_html=True
    )


def kpi_html(items):
    """items: list of dict(icon, label, value, color, sub)."""
    palette = [
        ("#533afd", "rgba(83, 58, 253, 0.08)"),
        ("#665efd", "rgba(102, 94, 253, 0.08)"),
        ("#9b6829", "rgba(155, 104, 41, 0.08)"),
        ("#00875a", "rgba(0, 135, 90, 0.08)"),
        ("#ea2261", "rgba(234, 34, 97, 0.08)"),
        ("#f96bee", "rgba(249, 107, 238, 0.12)"),
    ]
    cards = []
    for idx, it in enumerate(items):
        pal_color, pal_bg = palette[idx % len(palette)]
        val_color = it.get("color")
        if not val_color or val_color in ("#e8ecf4", "#60a5fa", "#38bdf8", "#a78bfa"):
            val_color = pal_color
        elif val_color == "#34d399":
            val_color = "#00875a"
        elif val_color in ("#fb923c", "#facc15"):
            val_color = "#9b6829"

        raw_icon = it.get("icon", "")
        # Resolve icon name to Lucide SVG name
        icon_name = ICON_MAP.get(raw_icon, raw_icon) if raw_icon else ""
        icon_html = f'<div class="kpi-icon-pill" style="background:{pal_bg};color:{val_color};">{icon(icon_name, 18, color=val_color)}</div>' if icon_name else ""
        sub = f'<div class="kpi-sub">{_e(strip_emoji(it["sub"]))}</div>' if it.get("sub") else ""
        clean_val = strip_emoji(it["value"])
        clean_lbl = strip_emoji(it["label"])
        cards.append(
            f'<div class="kpi">'
            f'<div class="kpi-top"><span class="kpi-label">{_e(clean_lbl)}</span>{icon_html}</div>'
            f'<div class="kpi-value" style="color:{val_color}">{_e(clean_val)}</div>'
            f'{sub}'
            f'</div>'
        )
    return '<div class="kpi-grid">' + "".join(cards) + "</div>"


def kpi_cards(items, container=None):
    (container or st).markdown(kpi_html(items), unsafe_allow_html=True)


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


def live_badge(active=True):
    cls = "live-badge" if active else "live-badge paused"
    txt = "LIVE" if active else "DIJEDA"
    st.markdown(f'<span class="{cls}"><span class="live-dot"></span>{txt}</span>', unsafe_allow_html=True)


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
    st.markdown('<div class="footer">Smart Farming Pakcoy · LSTM + CNN · data pelatihan sebagian simulasi</div>',
                unsafe_allow_html=True)
