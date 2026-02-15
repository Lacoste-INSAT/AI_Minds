# Synapsis — Design System & Component Strategy

> **Version**: 1.0  
> **Date**: 2026-02-14  
> **Author**: Frontend Lead (Person 1)  
> **Stack**: Next.js 16 + shadcn/ui + Tailwind CSS v4 + TypeScript  
> **Graph Viz**: react-force-graph (2D/3D)  
> **Icons**: Lucide React  

---

## 1. Design Philosophy

### 1.1 Core Principles

| Principle | Description |
|---|---|
| **Cognitive Calm** | A knowledge tool must reduce mental load, not add to it. Minimal chrome, generous whitespace, muted base tones with intentional pops of color for meaning. |
| **Information Density with Clarity** | Users deal with knowledge — text, graphs, timelines. Every pixel earns its place. Dense but never cluttered. |
| **Dark-First, Light-Ready** | Default to dark mode — it's where data visualization shines, graphs glow, and eyes rest during long sessions. Full light mode parity. |
| **Trust Through Transparency** | Confidence badges, source citations, and reasoning chains are first-class UI citizens — never hidden. |
| **Zero-Friction** | Zero upload buttons. Zero configuration noise after setup. The UI anticipates, not interrogates. |
| **Accessible by Default** | Keyboard navigable. WCAG 4.5:1 contrast. `prefers-reduced-motion` respected. Focus rings visible. |

### 1.2 Aesthetic Direction

**"Quiet Genius"** — The interface embodies the brand personality: intelligent, calm, and invisible.

- **Scientific Dashboard meets Obsidian**: A researcher's command center. Clean data surfaces.
- **Luminous Depth**: Glowing graph nodes and subtle gradients in dark mode creates a sense of "living data" (the Synapse metaphor).
- **Precision**: Monospace accents for technical data (confidence scores, timestamps). A UI that feels evidence-based.

- **NOT**: Playful / rounded / cartoon / startup-landing-page
- **IS**: Precise / architectural / data-driven / confident / beautiful restraint

---

## 2. Color System

### 2.1 Base Palette (oklch for shadcn/ui compatibility)

We use **Zinc** as the neutral base (cooler than Neutral, less blue than Slate — the sweet spot for data UIs).

#### Dark Mode (Primary)

```css
:root .dark {
  /* Base surfaces */
  --background:        oklch(0.12 0.005 260);    /* Deep blue-black */
  --foreground:        oklch(0.95 0 0);           /* Near-white text */
  
  /* Cards & panels */
  --card:              oklch(0.16 0.005 260);     /* Slightly lifted surface */
  --card-foreground:   oklch(0.95 0 0);
  
  /* Sidebar */
  --sidebar:           oklch(0.10 0.008 260);     /* Deepest surface */
  --sidebar-foreground: oklch(0.85 0 0);
  
  /* Muted (secondary text, disabled states) */
  --muted:             oklch(0.22 0.005 260);
  --muted-foreground:  oklch(0.65 0 0);
  
  /* Borders */
  --border:            oklch(1 0 0 / 8%);
  --input:             oklch(1 0 0 / 12%);
}
```

#### Light Mode

```css
:root {
  --background:        oklch(0.985 0.002 260);    /* Warm off-white */  
  --foreground:        oklch(0.15 0.005 260);     /* Near-black */
  --card:              oklch(1 0 0);              /* Pure white cards */
  --card-foreground:   oklch(0.15 0.005 260);
  --sidebar:           oklch(0.97 0.003 260);
  --sidebar-foreground: oklch(0.25 0.005 260);
  --muted:             oklch(0.96 0.002 260);
  --muted-foreground:  oklch(0.50 0.005 260);
  --border:            oklch(0 0 0 / 8%);
  --input:             oklch(0 0 0 / 12%);
}
```

### 2.2 Semantic Colors

These convey **meaning** across the entire application:

| Token | Purpose | Dark Mode | Light Mode |
|---|---|---|---|
| `--primary` | Main brand accent, active states, CTAs | `oklch(0.65 0.20 250)` — Electric Indigo | `oklch(0.50 0.22 250)` |
| `--primary-foreground` | Text on primary | `oklch(0.98 0 0)` | `oklch(0.98 0 0)` |
| `--accent` | Secondary highlights, hover states | `oklch(0.55 0.18 280)` — Soft Violet | `oklch(0.45 0.20 280)` |
| `--accent-foreground` | Text on accent | `oklch(0.98 0 0)` | `oklch(0.98 0 0)` |
| `--destructive` | Errors, REJECT verdicts, low confidence | `oklch(0.65 0.22 25)` — Warm Red | `oklch(0.55 0.24 25)` |

### 2.3 Confidence Badge Colors

Core to Synapsis UX — must be instantly recognizable:

| Confidence | Color Token | Dark Value | Light Value | Icon |
|---|---|---|---|---|
| **High** | `--confidence-high` | `oklch(0.72 0.19 155)` — Emerald | `oklch(0.55 0.20 155)` | `ShieldCheck` |
| **Medium** | `--confidence-medium` | `oklch(0.80 0.16 85)` — Amber | `oklch(0.65 0.18 85)` | `ShieldAlert` |
| **Low** | `--confidence-low` | `oklch(0.70 0.18 40)` — Orange | `oklch(0.58 0.20 40)` | `ShieldQuestion` |
| **None** | `--confidence-none` | `oklch(0.55 0 0)` — Gray | `oklch(0.50 0 0)` | `ShieldX` |

### 2.4 Entity Type Colors (Graph Nodes)

| Entity Type | Color | Hex Approximation | Usage |
|---|---|---|---|
| **Person** | Electric Blue | `#3B82F6` | Graph nodes, entity chips |
| **Organization** | Teal | `#14B8A6` | Graph nodes, entity chips |
| **Project** | Emerald Green | `#10B981` | Graph nodes, entity chips |
| **Concept** | Amber/Orange | `#F59E0B` | Graph nodes, entity chips |
| **Location** | Rose Pink | `#F43F5E` | Graph nodes, entity chips |
| **Date/Time** | Indigo | `#6366F1` | Graph nodes, entity chips |
| **Document** | Slate | `#94A3B8` | Graph nodes, entity chips |

### 2.5 Chart Colors (for Recharts via shadcn Chart)

```css
/* Dark mode chart palette — vibrant on dark surfaces */
--chart-1: oklch(0.65 0.24 265);   /* Indigo */
--chart-2: oklch(0.70 0.19 165);   /* Teal */
--chart-3: oklch(0.75 0.18 85);    /* Amber */
--chart-4: oklch(0.68 0.22 310);   /* Purple */
--chart-5: oklch(0.72 0.20 25);    /* Coral */
```

### 2.6 Luminous Effects (Brand Integration)

To achieve the "Quiet Genius" aesthetic (Luminous Depth), we define specific glow utilities. These are applied to high-confidence elements and the graph itself.

```css
/* Tailwind custom utilities */
.glow-primary {
  box-shadow: 0 0 20px -5px oklch(0.65 0.20 250 / 0.5);
}

.glow-node {
  /* Dynamic glow based on node color */
  filter: drop-shadow(0 0 8px currentColor);
}

.glass-panel {
  background: oklch(0.16 0.005 260 / 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid oklch(1 0 0 / 0.08);
}
```

---

## 3. Typography

### 3.1 Type Scale

| Role | Font | Weight | Size | Tracking |
|---|---|---|---|---|
| **H1** (Page titles) | Geist Sans | 700 (Bold) | 2rem / 32px | -0.02em |
| **H2** (Section headers) | Geist Sans | 600 (Semibold) | 1.5rem / 24px | -0.015em |
| **H3** (Card titles) | Geist Sans | 600 | 1.25rem / 20px | -0.01em |
| **Body** | Geist Sans | 400 (Regular) | 0.9375rem / 15px | 0 |
| **Body Small** | Geist Sans | 400 | 0.8125rem / 13px | 0 |
| **Caption/Label** | Geist Sans | 500 (Medium) | 0.75rem / 12px | 0.025em |
| **Monospace** (data, citations) | Geist Mono | 400 | 0.8125rem / 13px | 0 |
| **Chat Answer** | Geist Sans | 400 | 1rem / 16px | 0 |

### 3.2 Usage Rules

- **Geist Sans**: All UI text, headings, body, labels
- **Geist Mono**: Source citations `[Source 1]`, confidence scores, file paths, entity IDs, code snippets, timestamps
- **No other fonts** — two families maximum for visual cohesion

---

## 4. Spacing & Layout

### 4.1 Spacing Scale

Follow Tailwind's spacing scale consistently:

| Token | Value | Use Case |
|---|---|---|
| `gap-1` / `p-1` | 4px | Icon-to-text in badges |
| `gap-2` / `p-2` | 8px | Inner card padding, compact lists |
| `gap-3` / `p-3` | 12px | Between related items |
| `gap-4` / `p-4` | 16px | Standard card padding, section gaps |
| `gap-6` / `p-6` | 24px | Between sections, larger cards |
| `gap-8` / `p-8` | 32px | Page section spacing |

### 4.2 Layout Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Sidebar (collapsible, 16rem / icon-only)               │
│  ┌─────────┐ ┌──────────────────────────────────────┐   │
│  │ Logo    │ │ Main Content Area                     │   │
│  │ Nav     │ │ ┌──────────────────────────────────┐  │   │
│  │ items   │ │ │ Header bar (breadcrumb + actions) │  │   │
│  │         │ │ ├──────────────────────────────────┤  │   │
│  │ ──────  │ │ │                                  │  │   │
│  │ Status  │ │ │   View Content                   │  │   │
│  │ footer  │ │ │   (Chat / Graph / Timeline /     │  │   │
│  │         │ │ │    Setup / Search)                │  │   │
│  └─────────┘ │ │                                  │  │   │
│              │ └──────────────────────────────────┘  │   │
│              └──────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

- **Sidebar**: Left side, `collapsible="icon"` variant — collapses to icons only (saves space for graph/chat)
- **Main content**: Fills remaining width, padded with `p-6`
- **Resizable panels**: Used in Chat View (chat + source panel) and Graph Explorer (graph + detail panel)
- **Max width**: None — full viewport utilization for data-heavy views

### 4.3 Border Radius

```css
--radius: 0.625rem;  /* 10px — shadcn default, slightly rounded */
```

- Cards: `rounded-xl` (12px)
- Buttons: `rounded-lg` (8px)
- Badges: `rounded-full` (pill shape)
- Inputs: `rounded-lg` (8px)
- Modals/Sheets: `rounded-xl` (12px)

### 4.4 Shadow System

| Token | Value | Usage |
|---|---|---|
| `shadow-sm` | `0 1px 2px oklch(0 0 0 / 0.05)` | Badges, small elements |
| `shadow-md` | `0 4px 6px -1px oklch(0 0 0 / 0.1)` | **Default** — Cards, panels, popovers |
| `shadow-lg` | `0 10px 15px -3px oklch(0 0 0 / 0.12)` | Dialogs, elevated sheets |
| `shadow-glow` | See Section 2.6 | Graph nodes, active/selected elements |

In dark mode shadows are near-invisible; depth comes from **surface lightness levels** (Brand Identity §2.4) instead. Shadows are primarily useful in light mode.

### 4.5 Grid System

Use CSS Grid where needed (e.g. search results, settings pages):

```css
.grid-layout {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 1rem; /* gap-4 */
}
```

- **Timeline cards**: full-width (12 cols)
- **Search results (card mode)**: 4 cols per card on desktop (3-up), 6 cols on tablet (2-up), 12 cols on mobile (1-up)
- **Setup wizard**: centered 6-col content area
- **Most views**: Don't need the 12-col grid — they use Sidebar + Resizable panels (flexbox)

---

## 5. shadcn/ui Component Inventory

### 5.1 Core Layout Components

| Component | Install Command | Synapsis Usage |
|---|---|---|
| **Sidebar** | `npx shadcn@latest add sidebar` | Main navigation — Chat, Graph, Timeline, Setup, Search. Collapses to icons. Footer shows ingestion status. |
| **Resizable** | `npx shadcn@latest add resizable` | Chat View: split between chat and source panel. Graph Explorer: split between graph canvas and detail panel. |
| **Scroll Area** | `npx shadcn@latest add scroll-area` | Chat message list, timeline feed, source panel, sidebar content. Custom scrollbars everywhere. |
| **Tabs** | `npx shadcn@latest add tabs` | Sub-navigation within views. Timeline filters (All/Notes/PDF/Image/Audio/JSON). Source panel tabs (Evidence/Reasoning). |
| **Separator** | `npx shadcn@latest add separator` | Visual dividers between sidebar groups, between chat messages, in panels. |
| **Collapsible** | `npx shadcn@latest add collapsible` | "Why this answer" reasoning chain. Sidebar groups. Advanced filter panels. Setup wizard directory trees. |

### 5.2 Data Display Components

| Component | Install Command | Synapsis Usage |
|---|---|---|
| **Card** | `npx shadcn@latest add card` | Knowledge cards in timeline. Setup wizard step cards. Digest insight cards. Stats overview. |
| **Badge** | `npx shadcn@latest add badge` | Confidence badges (high/medium/low/none). Entity type chips. File modality tags. Verification status (APPROVE/REVISE/REJECT). |
| **Avatar** | `npx shadcn@latest add avatar` | Entity avatars in graph detail panel. Person nodes. Source document icons. |
| **Hover Card** | `npx shadcn@latest add hover-card` | Hover over entity chips → preview card with details. Hover over `[Source N]` → preview snippet. |
| **Tooltip** | `npx shadcn@latest add tooltip` | Toolbar icons, sidebar items when collapsed, confidence scores explanation, button hints. |
| **Table** | `npx shadcn@latest add table` | Ingestion status table (file, status, time). Search results in structured view. |
| **Skeleton** | `npx shadcn@latest add skeleton` | Loading states for chat answers, timeline cards, graph visualization, any async data fetch. |
| **Progress** | `npx shadcn@latest add progress` | File ingestion progress bar. Query processing indicator. Setup wizard progress. |
| **Spinner** | `npx shadcn@latest add spinner` | Inline loading in buttons. Chat "thinking" state. LLM processing indicator. |
| **Empty** | `npx shadcn@latest add empty` | No results found. Empty timeline. No graph data yet. First-run empty states before ingestion. |
| **Chart** | `npx shadcn@latest add chart` | Ingestion stats dashboard (files by type, over time). Knowledge graph stats. Confidence distribution. |

### 5.3 Interactive Components

| Component | Install Command | Synapsis Usage |
|---|---|---|
| **Button** | `npx shadcn@latest add button` | All actions — send query, navigate views, toggle panels, setup wizard steps. |
| **Input** | `npx shadcn@latest add input` | Chat input field. Search query box. Setup wizard directory path input. |
| **Textarea** | `npx shadcn@latest add textarea` | Extended question input (multi-line mode for complex queries). |
| **Select** | `npx shadcn@latest add select` | Timeline filter dropdowns (category, modality, date range). |
| **Checkbox** | `npx shadcn@latest add checkbox` | Setup wizard: select which directories to watch. Exclusion pattern toggles. |
| **Switch** | `npx shadcn@latest add switch` | Dark/light mode toggle. Enable/disable watched directories. Show advanced filters. |
| **Toggle Group** | `npx shadcn@latest add toggle-group` | View mode switches (2D/3D graph). Timeline view mode (cards/list). Filter mode. |
| **Slider** | `npx shadcn@latest add slider` | Graph zoom control. Timeline date range slider. Confidence threshold filter. |

### 5.4 Overlay Components

| Component | Install Command | Synapsis Usage |
|---|---|---|
| **Dialog** | `npx shadcn@latest add dialog` | Setup wizard modal (first-run). Confirmation dialogs. Knowledge card full detail view. |
| **Sheet** | `npx shadcn@latest add sheet` | Source citation panel (slides in from right). Node detail panel in graph. Mobile sidebar. |
| **Alert Dialog** | `npx shadcn@latest add alert-dialog` | Confirm directory removal. Confirm reset. Destructive action confirmations. |
| **Popover** | `npx shadcn@latest add popover` | Date pickers for timeline filters. Entity detail quick view. Settings mini-panel. |
| **Command** | `npx shadcn@latest add command` | Command palette / spotlight search (Cmd+K). Quick navigation across views. Fast entity/document lookup. |
| **Dropdown Menu** | `npx shadcn@latest add dropdown-menu` | Settings menu. Export options. Per-card actions. Sort options. |

### 5.5 Feedback Components

| Component | Install Command | Synapsis Usage |
|---|---|---|
| **Alert** | `npx shadcn@latest add alert` | Ingestion errors. Connection issues. Health check failures. Low confidence warnings. |
| **Sonner** (Toast) | `npx shadcn@latest add sonner` | Success notifications (file ingested). Error notifications. Status updates. "New insights available" prompts. |

### 5.6 Form Components

| Component | Install Command | Synapsis Usage |
|---|---|---|
| **Label** | `npx shadcn@latest add label` | Form field labels in setup wizard. Settings panel labels. |
| **Field** | `npx shadcn@latest add field` | Wraps label + input + description + error message. Used in setup wizard forms. |
| **Radio Group** | `npx shadcn@latest add radio-group` | Scan frequency selection. Model tier selection. |

### 5.7 Navigation Components

| Component | Install Command | Synapsis Usage |
|---|---|---|
| **Breadcrumb** | `npx shadcn@latest add breadcrumb` | Navigation trail: Home > Graph Explorer > Node Detail. Shows context in nested views. |

### 5.8 Additional Dependencies (non-shadcn)

| Package | Purpose | Priority |
|---|---|---|
| `react-force-graph` | Interactive 2D/3D knowledge graph visualization | P0 — core |
| `next-themes` | Dark/light mode theming with system detection | P0 — core |
| `lucide-react` | Icon library (already shadcn default) | P0 — core |
| `recharts` | Charts (used by shadcn Chart component internally) | P1 |
| `react-virtuoso` | Virtualized list rendering for chat messages & timeline feed — eliminates jank with 100+ items | P1 — perf |
| `react-pdf` | Render actual PDF pages in the source panel with highlighted passages (uses PDF.js under the hood) | P1 — demo wow |
| `browser-fs-access` | Polyfill/fallback for `showDirectoryPicker()` Web API — native folder picker in setup wizard | P1 — UX |
| `date-fns` | Lightweight date formatting & grouping for timeline ("Today", "Yesterday", "Feb 12"). Tree-shakeable, no heavy Moment.js. | P1 |
| `framer-motion` | Light animation polish: page transitions, list stagger, graph panel reveal. **P2 — only if time.** | P2 — polish |

---

## 6. Component-to-View Mapping

### 6.1 Chat View

```
┌──────────────────────────────────────────┬──────────────────┐
│  Chat Panel (Resizable)                  │  Source Panel     │
│  ┌────────────────────────────────────┐  │  (Resizable,     │
│  │ Virtuoso (virtualized message list) │  │  Sheet on mobile) │
│  │  ┌──────────────────────────────┐  │  │                  │
│  │  │ User message (Card, right)   │  │  │  Tabs:           │
│  │  └──────────────────────────────┘  │  │  - Evidence      │
│  │  ┌──────────────────────────────┐  │  │  - Reasoning     │
│  │  │ AI answer (Card)             │  │  │  - PDF Preview   │
│  │  │  - Markdown rendered text    │  │  │                  │
│  │  │  - [Source 1] [Source 2]     │  │  │  ScrollArea:     │
│  │  │    (Badge, clickable)        │  │  │  - ChunkEvidence │
│  │  │  - Confidence Badge          │  │  │    cards         │
│  │  │  - Verification status       │  │  │  - Score bars    │
│  │  │  - Collapsible: "Why this    │  │  │  - File name     │
│  │  │    answer" reasoning chain   │  │  │  - Snippet       │
│  │  └──────────────────────────────┘  │  │  - PDFViewer     │
│  └────────────────────────────────────┘  │    (when PDF src) │
│  ┌────────────────────────────────────┐  │                  │
│  │ Input bar                          │  │                  │
│  │  Textarea + Send Button + Spinner  │  │                  │
│  └────────────────────────────────────┘  │                  │
└──────────────────────────────────────────┴──────────────────┘
```

**Components used**: Resizable, Virtuoso (react-virtuoso), Card, Badge (confidence + verification + source), Collapsible, Textarea, Button, Spinner, Tabs, Skeleton (loading), HoverCard (source preview), Tooltip, PDFViewer (react-pdf — in source panel for PDF sources)

### 6.2 Graph Explorer

```
┌──────────────────────────────────────────┬──────────────────┐
│  Graph Canvas (Resizable)                │  Detail Panel    │
│  ┌────────────────────────────────────┐  │  (Resizable)     │
│  │                                    │  │                  │
│  │   react-force-graph (2D/3D)        │  │  Card:           │
│  │   - Color-coded nodes              │  │  - Entity name   │
│  │   - Labeled edges                  │  │  - Type badge    │
│  │   - Click to select                │  │  - Properties    │
│  │   - Hover for tooltip              │  │  - Connected     │
│  │                                    │  │    nodes list    │
│  └────────────────────────────────────┘  │  - Source docs   │
│  ┌────────────────────────────────────┐  │  - Timeline of   │
│  │ Controls bar                       │  │    mentions      │
│  │  ToggleGroup: 2D/3D               │  │                  │
│  │  Slider: zoom                      │  │  Empty: when no  │
│  │  Select: filter by entity type     │  │  node selected   │
│  │  Button: reset view                │  │                  │
│  └────────────────────────────────────┘  │                  │
└──────────────────────────────────────────┴──────────────────┘
```

**Components used**: Resizable, Card, Badge (entity type), ToggleGroup, Slider, Select, Button, Tooltip, ScrollArea, Empty, Skeleton

### 6.3 Timeline View

```
┌─────────────────────────────────────────────────────────┐
│  Filter Bar                                              │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Tabs: All | Notes | PDFs | Images | Audio | JSON   │ │
│  │ Select: Category | Select: Date Range              │ │
│  │ Input: Search within timeline                      │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Virtuoso — Virtualized Knowledge Card Feed          │ ││  │                                                     │ │
│  │  ─── Today ────────────────────────────────  │ ││  │  ┌───────────────────────────────────────────────┐  │ │
│  │  │ Card (Knowledge Card)                         │  │ │
│  │  │  - Title + Badge (modality) + Badge (category)│  │ │
│  │  │  - Summary text                               │  │ │
│  │  │  - Entity chips (clickable → graph)           │  │ │
│  │  │  - Action items (Collapsible)                 │  │ │
│  │  │  - Timestamp (Geist Mono)                     │  │ │
│  │  └───────────────────────────────────────────────┘  │ │
│  │  ┌───────────────────────────────────────────────┐  │ │
│  │  │ Card ...                                      │  │ │
│  │  └───────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
│  Empty: "No memories yet — drop files in watched dirs"   │
└─────────────────────────────────────────────────────────┘
```

**Components used**: Tabs, Select, Input, Virtuoso (react-virtuoso), Card, Badge (modality + category), Collapsible, Button, Empty, Skeleton, Tooltip, HoverCard

**Date grouping**: Cards are grouped by date using `date-fns` (`isToday`, `isYesterday`, `format`). Each group has a sticky Separator label: "Today", "Yesterday", "Feb 12, 2026", etc. Virtuoso's `groupCounts` + `groupContent` props handle this natively.

### 6.4 Setup Wizard

```
┌─────────────────────────────────────────────────────────┐
│  Dialog (full-screen on first run)                       │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Progress indicator (step 1/3, 2/3, 3/3)            │ │
│  ├─────────────────────────────────────────────────────┤ │
│  │ STEP 1: Welcome                                    │ │
│  │  - Branding + description                          │ │
│  │  - "Get Started" Button                            │ │
│  ├─────────────────────────────────────────────────────┤ │
│  │ STEP 2: Choose Directories                         │ │
│  │  - Checkbox list: ~/Documents, ~/Desktop, etc.     │ │
│  │  - Button: "Browse..." → showDirectoryPicker() API  │ │
│  │    (native OS folder dialog, browser-fs-access      │ │
│  │     fallback for unsupported browsers)              │ │
│  │  - Input: Manual path entry as alternative          │ │
│  │  - Button: "Add Directory"                         │ │
│  ├─────────────────────────────────────────────────────┤ │
│  │ STEP 3: Exclusions (optional)                      │ │
│  │  - Checkbox list: common exclusions                │ │
│  │  - Input: custom glob patterns                     │ │
│  │  - Collapsible: advanced options (max file size)   │ │
│  ├─────────────────────────────────────────────────────┤ │
│  │ Footer: Back / Next / Finish buttons               │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Components used**: Dialog, Progress, Card, Checkbox, Input, Button, Collapsible, Label, Field, Separator, Alert (tips/warnings)

### 6.5 Search + Filters View

```
┌─────────────────────────────────────────────────────────┐
│  Command (Spotlight-style search bar)                    │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ CommandInput: full-text search across knowledge     │ │
│  │ CommandList:                                        │ │
│  │   CommandGroup "Entities" — entity matches          │ │
│  │   CommandGroup "Documents" — document matches       │ │
│  │   CommandGroup "Actions" — view navigation          │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Filter Panel                                       │ │
│  │  Select: Entity type | Select: Modality             │ │
│  │  Select: Category | Date range picker               │ │
│  │  Button: Clear All                                  │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Results — Card list or Table view                   │ │
│  │  ToggleGroup: Card view / Table view                │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Components used**: Command, Select, Button, Card, Table, ToggleGroup, Badge, ScrollArea, Empty, Skeleton

---

## 7. Shared Custom Components

These are composite components built from shadcn primitives — reusable across all views:

### 7.1 `<ConfidenceBadge>`

```
Props: level ("high" | "medium" | "low" | "none"), score (number)
Renders: Badge with icon + label + tooltip showing exact score
Colors: confidence-high/medium/low/none semantic tokens
```

### 7.2 `<EntityChip>`

```
Props: name (string), type (string), onClick?
Renders: small pill badge, color-coded by entity type
Hover: HoverCard with entity details preview
Click: Navigate to Graph Explorer with entity focused
```

### 7.3 `<SourceCitation>`

```
Props: source (ChunkEvidence), index (number)
Renders: [Source N] as a clickable monospace badge  
Click: Opens source panel & highlights the relevant chunk
Hover: HoverCard with snippet preview
```

### 7.4 `<VerificationBadge>`

```
Props: status ("APPROVE" | "REVISE" | "REJECT")
Renders: Badge with icon
  APPROVE → green check
  REVISE → amber refresh
  REJECT → red X
```

### 7.5 `<KnowledgeCard>`

```
Props: card (KnowledgeCard data)
Renders: Card with title, summary, entity chips, modality badge, 
         category badge, action items (collapsible), timestamp
Used in: Timeline View, Search results
```

### 7.6 `<IngestionStatus>`

```
Props: status data from /ingestion/status
Renders: Sidebar footer mini-display
  - Files in queue count (Badge)
  - Processing spinner when active
  - "Last scan: 2min ago" text
  - Click: expand to full ingestion view
```

### 7.7 `<HealthIndicator>`

```
Props: health data from /health
Renders: Dot indicator (green/yellow/red)
  - Tooltip with full health breakdown
  - Ollama status, Qdrant status, SQLite status
```

### 7.8 `<PDFViewer>`

```
Props: fileUrl (string), highlightText? (string), page? (number)
Renders: Embedded PDF page via react-pdf (PDF.js).
  - Renders only the relevant page (not the full document)
  - Highlights the cited passage with a translucent overlay
  - Lazy-loads PDF.js worker for performance
  - Fallback: plain text snippet if PDF rendering fails
Used in: Source panel (Evidence tab) when source is a PDF
```

### 7.9 `<SourceViewer>`

```
Props: content (string), language? (string), highlights? (Range[]), fileType ("text" | "pdf" | "code" | "markdown")
Renders: Multi-format source evidence viewer
  - PDF: delegates to <PDFViewer>
  - Code/Markdown: renders with syntax highlighting (Shiki, bundled with Next.js)
  - Plain text: renders in Geist Mono with highlight overlay on cited spans
  - Always shows file name, modality badge, and relevance score
Used in: Source panel (Evidence tab)
```

### 7.10 `<DirectoryPicker>`

```
Props: value (string[]), onChange (dirs => void)
Renders: List of selected directories + "Browse..." button
  - Uses showDirectoryPicker() Web API when supported
  - Falls back to browser-fs-access for older browsers
  - Manual path input as last resort
  - Each entry has a remove (X) button
Used in: Setup Wizard step 2
```

---

## 8. Animation & Motion

### 8.1 Transitions

| Element | Transition | Duration | Easing |
|---|---|---|---|
| Sidebar collapse | Width | 200ms | `ease-linear` (shadcn default) |
| Panel resize | Width/Height | 0ms (real-time drag) | — |
| Page transitions | Opacity + translateY | 150ms | `ease-out` |
| Card hover | Scale + shadow | 150ms | `ease-out` |
| Badge appear | Opacity + scale | 100ms | `ease-out` |
| Skeleton pulse | Opacity | 1.5s | `ease-in-out` (loop) |
| Graph nodes | Physics simulation | continuous | spring-based |
| Toast slide | translateX | 200ms | `ease-out` |

### 8.2 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- Graph falls back to static layout (no physics simulation)
- Skeleton uses static gray instead of pulse
- All transitions become instant

---

## 9. Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|---|---|---|
| **Mobile** | < 768px | Sidebar becomes sheet overlay. Resizable panels stack vertically. Source panel becomes bottom sheet. Graph controls become floating toolbar. |
| **Tablet** | 768px–1024px | Sidebar icon-only by default. Panels side-by-side but narrower. |
| **Desktop** | 1024px–1440px | Full layout. Sidebar expanded. All panels visible. |
| **Wide** | > 1440px | Extra whitespace utilized. Wider panels. |

---

## 10. Dark/Light Mode Implementation

Using `next-themes` (as per shadcn/ui docs):

1. Install: `npm install next-themes`
2. Create `ThemeProvider` wrapper component
3. Wrap root layout
4. Use `Switch` component for manual toggle in sidebar footer
5. Default: `system` (auto-detect OS preference)
6. Persist choice in `localStorage`

---

## 11. Accessibility Checklist

| # | Requirement | Implementation |
|---|---|---|
| A11Y-1 | Keyboard navigation | All shadcn components have built-in keyboard support. Tab order follows visual order. Arrow keys within composite widgets (Tabs, ToggleGroup, RadioGroup). |
| A11Y-2 | Focus indicators | Default shadcn focus rings (`ring` utility). High contrast ring on primary color. |
| A11Y-3 | Color contrast | WCAG AA minimum (4.5:1 for text). All semantic colors tested with oklch contrast checker. |
| A11Y-4 | Screen reader | All interactive elements have `aria-label`. Badges use `sr-only` text. Icons have alt text. |
| A11Y-5 | Reduced motion | `prefers-reduced-motion` media query respects system setting. |
| A11Y-6 | Skip links | "Skip to main content" link at top of page. |
| A11Y-7 | Semantic HTML | Proper heading hierarchy. `<main>`, `<nav>`, `<aside>` landmarks. |
| A11Y-8 | Live regions | Chat new messages use `aria-live="polite"`. Ingestion status updates use `aria-live="assertive"` for errors. |

### 11.1 ARIA Patterns for Key Interactions

| Component | ARIA Pattern | Notes |
|---|---|---|
| **Command palette** (Cmd+K) | `role="combobox"` + `aria-activedescendant` | shadcn Command uses cmdk internally, which implements the W3C APG Combobox pattern. Focus stays on input, arrow keys move `aria-activedescendant`. |
| **Dialogs** (Setup wizard, confirmations) | `role="dialog"` + `aria-modal="true"` | Radix Dialog handles focus trap, `Escape` to close, return focus on dismiss. |
| **Chat message list** | `role="log"` + `aria-live="polite"` | New messages announced without interrupting. Virtuoso handles dynamic content. |
| **Graph canvas** | `role="img"` + `aria-label` | Canvas-based rendering is not accessible; provide an accessible alternative via the detail panel (table of entities + relationships). |
| **Sidebar nav** | `role="navigation"` + `aria-label="Main"` | Collapsible state communicated via `aria-expanded`. |
| **Confidence badges** | `aria-label="Confidence: high, score 0.92"` | Ensure color is never the sole indicator — icon + label + tooltip. |

---

## 12. Full Installation Command

Run this to install all needed shadcn components in one go:

```bash
npx shadcn@latest add sidebar resizable scroll-area tabs separator collapsible card badge avatar hover-card tooltip table skeleton progress spinner empty chart button input textarea select checkbox switch toggle-group slider dialog sheet alert-dialog popover command dropdown-menu alert sonner label field radio-group breadcrumb accordion
```

Additional npm packages:

```bash
npm install react-force-graph next-themes lucide-react recharts react-virtuoso react-pdf browser-fs-access framer-motion date-fns
```

---

## 13. File Structure (Frontend)

```
frontend/synapsis/
├── app/
│   ├── layout.tsx          # Root layout + ThemeProvider + SidebarProvider + TooltipProvider
│   ├── page.tsx            # Redirect to /chat or /setup (if first run)
│   ├── globals.css         # CSS variables, custom tokens, tailwind base
│   ├── chat/
│   │   └── page.tsx        # Chat View
│   ├── graph/
│   │   └── page.tsx        # Graph Explorer
│   ├── timeline/
│   │   └── page.tsx        # Timeline View
│   ├── search/
│   │   └── page.tsx        # Search + Filters
│   └── setup/
│       └── page.tsx        # Setup Wizard
├── components/
│   ├── ui/                 # shadcn components (auto-generated)
│   ├── layout/
│   │   ├── app-sidebar.tsx # Main sidebar navigation
│   │   └── header.tsx      # Top header with breadcrumb + actions
│   ├── chat/
│   │   ├── chat-input.tsx
│   │   ├── chat-message.tsx
│   │   ├── source-panel.tsx
│   │   ├── pdf-viewer.tsx
│   │   └── answer-card.tsx
│   ├── graph/
│   │   ├── graph-canvas.tsx
│   │   ├── graph-controls.tsx
│   │   └── node-detail.tsx
│   ├── timeline/
│   │   ├── timeline-feed.tsx
│   │   ├── timeline-filters.tsx
│   │   └── knowledge-card.tsx
│   ├── setup/
│   │   ├── wizard-steps.tsx
│   │   └── directory-picker.tsx
│   └── shared/
│       ├── confidence-badge.tsx
│       ├── entity-chip.tsx
│       ├── source-citation.tsx
│       ├── verification-badge.tsx
│       ├── health-indicator.tsx
│       ├── ingestion-status.tsx
│       ├── pdf-viewer.tsx
│       ├── directory-picker.tsx
│       └── theme-toggle.tsx
├── hooks/
│   ├── use-query.ts        # POST /query/ask hook
│   ├── use-timeline.ts     # GET /memory/timeline hook
│   ├── use-graph.ts        # GET /memory/graph hook
│   ├── use-config.ts       # GET/PUT /config/sources hook
│   ├── use-health.ts       # GET /health hook
│   └── use-ingestion.ts    # GET /ingestion/status + WebSocket hook
├── lib/
│   ├── utils.ts            # cn() helper (shadcn)
│   ├── api.ts              # API client (fetch wrapper for localhost:8000)
│   └── constants.ts        # Entity colors, confidence levels, etc.
└── types/
    └── index.ts            # TypeScript types matching backend data contracts
```

---

## 14. Install Priority Order

| Phase | Components | Why First |
|---|---|---|
| **Phase 0** | button, input, badge, card, skeleton, spinner | Base primitives used everywhere |
| **Phase 1** | sidebar, scroll-area, separator, tabs, tooltip, sonner | Navigation shell + layout |
| **Phase 2** | resizable, collapsible, sheet, dialog, textarea | Chat View + panels |
| **Phase 3** | select, checkbox, switch, toggle-group, slider, label, field, progress, alert, command | Timeline filters + Setup wizard + Search |
| **Phase 4** | hover-card, breadcrumb, dropdown-menu, popover, chart, table, empty, accordion, alert-dialog, radio-group | Polish + secondary features |
