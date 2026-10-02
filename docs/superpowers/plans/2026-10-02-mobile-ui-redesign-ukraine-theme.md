# Mobile UI/UX Redesign & Ukrainian Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign `apps_script/Index.html` into a mobile-first, thumb-friendly interface featuring a Ukrainian flag color palette (Azure Blue & Sunflower Gold), adaptive signature canvas, simplified "Kirim SPT" button, and responsive mobile bottom navigation.

**Architecture:** Single-page progressive web interface built on Tailwind CSS and vanilla JavaScript. Retains 100% compatibility with Google Apps Script server methods in `Code.js`. Enhances layout with a mobile bottom navigation bar, responsive canvas sizing with Retina support, and mobile card view for admin submissions.

**Tech Stack:** HTML5, Tailwind CSS, Google Fonts (Outfit), Canvas API, SweetAlert2, Google Apps Script client API (`google.script.run`).

## Global Constraints

- Never change or break existing form input `name` attributes and element `id`s expected by `Code.js` (`sptForm`, `opd-select`, `kegiatan-select`, `dasar-textarea`, `pangkat-select`, `pangkat-atasan-select`, `sig-canvas`, etc.).
- Never break SweetAlert2 modal dialogs or canvas signature capture data URLs.
- Submit button text must be simply "Kirim SPT".
- Follow Ukrainian flag color palette: Azure Blue (`#0057B7`), Deep Blue (`#00438F`), Sunflower Gold/Amber (`#F59E0B`, `#FFD700`).

---

### Task 1: Ukrainian Color Theme & Mobile Base Styles Setup

**Files:**
- Modify: `apps_script/Index.html:1-120`

**Interfaces:**
- Consumes: Tailwind CDN script, Google Font Outfit.
- Produces: CSS variables and custom utility classes for Ukraine Azure Blue (`#0057B7`), Sunflower Gold (`#F59E0B`, `#FFD700`), high-contrast dark text (`#0F172A`), responsive container offsets (`pb-28`).

- [ ] **Step 1: Define Tailwind custom color config and theme CSS variables**
  Update `<style>` block in `Index.html` to define `--color-ua-blue`, `--color-ua-gold`, `--color-ua-blue-dark`, and configure Tailwind custom classes (`bg-ua-blue`, `text-ua-blue`, `border-ua-blue`, etc.).
- [ ] **Step 2: Add mobile safe-area styling and smooth focus outlines**
  Add styles for bottom nav dock (`bottom-nav`), touch-action rules, and input touch height (min 48px).
- [ ] **Step 3: Verify syntax**
  Check HTML structure and styling tags.
- [ ] **Step 4: Commit**
  `git commit -am "style: add Ukraine color tokens and mobile base styles"`

---

### Task 2: Sticky Top Header & Mobile Bottom Navigation Bar

**Files:**
- Modify: `apps_script/Index.html:120-160` and script section around tab switching.

**Interfaces:**
- Consumes: `switchTab(tabId)` function.
- Produces: Synced desktop tab pills + mobile bottom dock buttons (`mobile-nav-operator`, `mobile-nav-admin`).

- [ ] **Step 1: Refactor Top Header**
  Create a clean sticky top bar with logo, title "KIRIM SPT DIGITAL", subtitle, and desktop-only tab pills.
- [ ] **Step 2: Add Mobile Bottom Navigation Bar**
  Add fixed bottom navigation bar for mobile (`md:hidden`) with icons + labels for "Form SPT" and "Panel Admin".
- [ ] **Step 3: Update `switchTab` JavaScript**
  Update `switchTab(tabId)` to toggle active visual states on both desktop top buttons and mobile bottom dock buttons simultaneously.
- [ ] **Step 4: Verify tab switching behavior**
  Verify switching between operator and admin tabs works seamlessly on both mobile dock and desktop header.
- [ ] **Step 5: Commit**
  `git commit -am "feat: implement sticky top bar and mobile bottom navigation bar"`

---

### Task 3: Operator Form Mobile Optimization & Simplified "Kirim SPT" Button

**Files:**
- Modify: `apps_script/Index.html:150-375`

**Interfaces:**
- Consumes: `#sptForm`, `handleFormSubmit(event)`.
- Produces: Clean section headers with Ukraine Blue/Gold numbered badges, min-48px inputs, and simplified button labeled "Kirim SPT".

- [ ] **Step 1: Upgrade section headers with numbered badges**
  Wrap sections (I. Unit Kerja & Perihal, II. Profil Admin, III. Profil Atasan, IV. Tanda Tangan Atasan) with numbered pill badges.
- [ ] **Step 2: Optimize input fields and selects for touch targets**
  Apply min 48px height, `text-base` font size to prevent mobile auto-zoom, and smooth blue focus ring.
- [ ] **Step 3: Update submit button text and styling**
  Change button `#btn-submit-spt` content to **"Kirim SPT"** with vibrant Ukrainian Azure Blue styling (`bg-[#0057B7]` hover `bg-[#00438F]`) and soft gold active ring.
- [ ] **Step 4: Commit**
  `git commit -am "feat: optimize operator form touch targets and rename submit button to Kirim SPT"`

---

### Task 4: Dynamic Retina-Ready Responsive Signature Canvas

**Files:**
- Modify: `apps_script/Index.html:345-365` and script section for signature pad.

**Interfaces:**
- Consumes: Canvas element `#sig-canvas`.
- Produces: Responsive canvas that dynamically matches container width and scales by `window.devicePixelRatio`.

- [ ] **Step 1: Update canvas container and HTML attributes**
  Set `#sig-canvas` style to `w-full` with max width constraint, removing hardcoded fixed width.
- [ ] **Step 2: Implement dynamic canvas resizing in JavaScript**
  Create `resizeCanvas()` function that adjusts internal canvas pixel buffer to match display width multiplied by `window.devicePixelRatio` while preserving existing strokes.
- [ ] **Step 3: Test drawing and clear functions**
  Ensure touch and mouse drawing work accurately at all screen sizes.
- [ ] **Step 4: Commit**
  `git commit -am "feat: implement dynamic responsive retina signature canvas"`

---

### Task 5: Panel Admin Mobile Responsiveness & Ukrainian Theme Styling

**Files:**
- Modify: `apps_script/Index.html:375-570`

**Interfaces:**
- Consumes: `submissionsDb`, `renderTable()`, `renderStats()`, `renderProgress()`.
- Produces: Responsive admin UI with 2-col mobile KPI stats, mobile card view for submissions, and Ukraine color scheme.

- [ ] **Step 1: Restyle Admin Login Box & Sub-tab Pill Switchers**
  Update login form and sub-tabs (`submisi-panel` vs `kegiatan-panel`) with modern segmented control pill design.
- [ ] **Step 2: Update KPI Stats Cards for Mobile Grid**
  Ensure KPI cards display in a 2-column grid on mobile (`grid-cols-2 md:grid-cols-4`).
- [ ] **Step 3: Implement Mobile Card View for Submissions**
  Add mobile-friendly card list representation (`block md:hidden`) alongside desktop table (`hidden md:table`) in `#submission-tbody` or container so mobile users can view and download submissions effortlessly.
- [ ] **Step 4: Update all button styles and status badges**
  Replace indigo tones with Ukraine Azure Blue and Sunflower Gold badges across admin panel.
- [ ] **Step 5: Commit**
  `git commit -am "feat: adapt admin panel for mobile with responsive submission cards and Ukraine palette"`

---

### Task 6: Final Verification & Theme Polish

**Files:**
- Modify: `apps_script/Index.html`

- [ ] **Step 1: Syntax and script integrity check**
  Run node script to ensure no JavaScript parse errors.
- [ ] **Step 2: Responsive viewport verification**
  Verify page rendering and layout across mobile (360px-414px) and desktop (>1024px) viewport sizes.
- [ ] **Step 3: Commit and finalize**
  `git commit -am "chore: finalize mobile UI redesign and Ukraine theme polish"`
