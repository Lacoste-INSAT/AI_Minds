# Synapsis — Brand Identity & UX Strategy

> **Version**: 1.0  
> **Date**: 2026-02-14  
> **Purpose**: Brand guidelines, visual identity, UX micro-copy, emotional design, and presentation strategy  
> **Audience**: All team members, demo presenters, judges  

---

## 1. Brand Essence

### 1.1 Name: **Synapsis**

**Etymology**: From Greek *σύναψις* (synapsis) — "a point of connection." In neuroscience, a synapse is the junction where neurons communicate. Synapsis is the junction where your ideas connect.

**The name captures**:

- **Connection** — linking ideas, people, projects across your documents
- **Intelligence** — neural, cognitive, brain-like processing
- **Organic growth** — your knowledge graph evolves as you think
- **Science** — grounded, evidence-based, not magical

### 1.2 Tagline Options

| Tagline | Context |
|---|---|
| **"Your knowledge, connected."** | Primary — for hero/landing/about |
| **"Think once. Remember forever."** | Emotional — for pitch deck |
| **"Zero effort. Total recall."** | Feature-focused — emphasizes zero-touch |
| **"The memory you deserve."** | Personal — emphasizes individual empowerment |

**Recommended primary**: **"Your knowledge, connected."**

### 1.3 Brand Personality

Synapsis is a **quiet genius** — it doesn't shout, it reveals.

| Trait | Expression |
|---|---|
| **Intelligent** | Dense, well-organized data. No fluff. Precise language. |
| **Calm** | Muted palette. Generous whitespace. No urgent red banners. |
| **Trustworthy** | Always shows its work — sources, confidence, reasoning. Never fabricates. |
| **Invisible** | The best feature is what you DON'T do — never upload, never configure, never maintain. |
| **Empowering** | Your data, your machine, your control. Air-gapped. Sovereign. |

### 1.4 Brand Voice

| Do | Don't |
|---|---|
| "I found 3 sources related to this." | "I think the answer might be..." |
| "Confidence: medium — 2 sources agree, 1 is outdated." | "I'm pretty sure about this!" |
| "I don't have enough information to answer this." | "Sorry, I can't help with that." |
| "New connection discovered between 'Sarah' and 'marketing budget'." | "Hey! Check out this cool finding!" |
| "Processing 12 files from ~/Documents..." | "Hang tight! We're crunching your data!" |

**Tone**: **Professional, helpful, transparent, never casual.**

---

## 2. Visual Identity

### 2.1 Logo Concept

**Mark**: An abstract synapse — two nodes connected by a luminous arc. Represents the core metaphor: ideas connecting.

```
     ●━━━━━━━━●
    ╱            ╲
   ╱   SYNAPSIS   ╲
```

**Design specifications**:

- **Shape**: Two circles (nodes) connected by a curved line (edge) with a subtle glow at the center
- **Style**: Geometric, minimal, single-stroke weight
- **Minimum size**: 24x24px (favicon), scales to any size
- **Clear space**: 1x the node diameter on all sides

**Logo Variants**:

| Variant | Use Case |
|---|---|
| **Icon only** (two connected nodes) | Favicon, sidebar collapsed, app icon, loading screen |
| **Icon + wordmark** (horizontal) | Sidebar header expanded, setup wizard, about page |
| **Wordmark only** | When space is tight, text contexts |

### 2.2 Color Identity

#### Primary Brand Color: **Electric Indigo**

```
Light:  oklch(0.50 0.22 250)  →  ~#4338CA  
Dark:   oklch(0.65 0.20 250)  →  ~#6366F1
```

Why indigo:

- **Scientific** — associated with precision, intelligence, depth
- **Not overused** — blue is everywhere; indigo stands apart
- **Graph glow** — looks stunning as node highlights on dark backgrounds
- **Accessible** — passes WCAG on both dark and light surfaces
- **Versatile** — pairs well with warm accents (amber, coral) for contrast

#### Secondary Brand Color: **Soft Violet**

```
Light:  oklch(0.45 0.20 280)  →  ~#7C3AED
Dark:   oklch(0.55 0.18 280)  →  ~#8B5CF6
```

Used for: hover states, secondary actions, graph edge highlights, accent elements.

#### Signal Colors

| Signal | Color | Meaning in Synapsis |
|---|---|---|
| **Emerald** | `#10B981` / `#34D399` | High confidence, APPROVE, success, healthy |
| **Amber** | `#F59E0B` / `#FBBF24` | Medium confidence, REVISE, warning, processing |
| **Red/Coral** | `#EF4444` / `#F87171` | Low/no confidence, REJECT, error, unhealthy |
| **Sky Blue** | `#0EA5E9` / `#38BDF8` | Info, links, entity highlights |

### 2.3 Dark Mode as Default

Synapsis defaults to dark mode. This is a deliberate brand decision:

1. **Luminous Depth** — colored nodes with glow effects (Design System 2.6) create a "living data" feel vs flat static pages.
2. **Scientific Dashboard** — aligns with high-density data tools (Bloomberg, Grafana) where dark is standard for power users.
3. **Eye comfort** — knowledge workers often spend hours reading; dark reduces strain.
4. **Brand distinction** — most hackathon projects use white backgrounds (SaaS default); we stand out as a pro-tool.
5. **The "wow" factor** — 3D graph visualization with glowing nodes in dark mode is visually striking for judges

Light mode is fully supported but secondary.

### 2.4 Surface Hierarchy (Dark Mode)

```
Level 0 — Page background:        oklch(0.10)     ████████████
Level 1 — Sidebar:                oklch(0.08)     ████████████  (deepest)
Level 2 — Cards, panels:          oklch(0.14)     ████████████
Level 3 — Elevated (hover, popover): oklch(0.18)  ████████████
Level 4 — Highest (dialog overlay):  oklch(0.22)  ████████████
```

Each level is subtly lighter, creating depth without borders. The sidebar is the darkest surface, grounding the navigation.

### 2.5 Iconography

**Library**: Lucide React (shadcn/ui default)

| View/Feature | Icon | Lucide Name |
|---|---|---|
| Chat View | `MessageSquare` | message-square |
| Graph Explorer | `Network` | network |
| Timeline | `Clock` | clock |
| Setup Wizard | `Settings` | settings |
| Search | `Search` | search |
| Ingestion Status | `HardDrive` | hard-drive |
| Health | `Activity` | activity |
| Dark/Light toggle | `Moon` / `Sun` | moon / sun |
| Source citation | `FileText` | file-text |
| Confidence High | `ShieldCheck` | shield-check |
| Confidence Medium | `ShieldAlert` | shield-alert |
| Confidence Low | `ShieldQuestion` | shield-question |
| Confidence None | `ShieldX` | shield-x |
| Approve | `CheckCircle` | check-circle |
| Revise | `RefreshCw` | refresh-cw |
| Reject | `XCircle` | x-circle |
| Person entity | `User` | user |
| Org entity | `Building` | building |
| Concept entity | `Lightbulb` | lightbulb |
| Document entity | `File` | file |
| Send message | `Send` | send |
| Expand/Collapse | `ChevronDown` | chevron-down |
| Directory | `Folder` | folder |
| Add | `Plus` | plus |
| Remove | `Trash2` | trash-2 |

**Icon style rules**:

- Size: 16px (`size-4`) for inline, 20px (`size-5`) for buttons, 24px (`size-6`) for sidebar
- Stroke width: 1.75px (default Lucide)
- Color: inherit from parent text color
- Never use filled icons — always outline/stroke for consistency

---

## 3. UX Strategy

### 3.1 First-Run Experience (Critical — Judges will see this)

The first-run experience IS the demo. It must be flawless.

**Flow**:

```
App opens → Setup Wizard appears (full-screen Dialog)
  │
  ├─ Step 1: WELCOME
  │  "Welcome to Synapsis"
  │  "Your knowledge, connected."
  │  Brief animation: two nodes connecting
  │  [Get Started] button
  │
  ├─ Step 2: CHOOSE DIRECTORIES
  │  "What folders should Synapsis watch?"
  │  Pre-checked: ~/Documents, ~/Desktop, ~/Downloads
  │  [Browse...] button → native OS folder picker dialog
  │  (uses showDirectoryPicker() API — feels native, not webby)
  │  Manual path input as fallback
  │  Subtle note: "Files are read-only — Synapsis never modifies your files."
  │
  ├─ Step 3: EXCLUSIONS (optional, collapsible)
  │  "Anything you want to skip?"
  │  Common presets: node_modules, .git, executables
  │  Custom glob pattern input
  │  [Skip] or [Apply] buttons
  │
  └─ Step 4: DONE
     "You're all set."
     "Synapsis is now watching your directories."
     Progress bar showing initial scan
     [Open Synapsis] → navigates to Chat view
```

**UX Principles for Setup**:

- **Never intimidating** — friendly language, clear defaults, skip option for advanced stuff
- **Fast** — 3 clicks minimum to complete (Get Started → confirm dirs → Open)
- **Trustworthy** — explicitly state "read-only, never modifies your files"
- **Visual feedback** — progress bar during initial scan so user knows something is happening

### 3.2 Chat View UX

The chat is the **primary view** — users spend 80% of time here.

**Input UX**:

- Auto-focus on page load
- `Enter` to send, `Shift+Enter` for new line
- Placeholder: *"Ask anything about your knowledge..."*
- Disable send while processing (spinner replaces send icon)
- Max textarea height: 120px, then scrolls

**Answer UX**:

- **Streaming**: Tokens appear as they arrive (WebSocket)
- **Skeleton**: While waiting for first token, show animated skeleton with 3 pulsing lines
- **Citations inline**: `[Source 1]` rendered as clickable badges within the answer text
- **Confidence badge**: Always visible, bottom-left of answer card
- **Verification badge**: Always visible, next to confidence
- **"Why this answer"**: Collapsible section at bottom of answer — shows reasoning chain
- **Source panel**: Opens when clicking any `[Source N]` — shows full chunk with highlight
- **PDF source**: If the source is a PDF, render the actual PDF page with the cited passage highlighted (react-pdf). This is a massive demo differentiator — judges see real PDF rendering, not just extracted text.
- **Code/Markdown source**: Syntax-highlighted with Shiki (bundled with Next.js) — shows actual code files with highlighted lines instead of plain text dumps.

**Abstention UX** (when confidence = "none"):

```
┌──────────────────────────────────────────┐
│ ShieldX  I don't have enough information │
│          to answer this confidently.     │
│                                          │
│  Here's what I found that might help:    │
│  ┌────────────────────────────────────┐  │
│  │ Partial result cards (low opacity) │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Confidence: None ░░░░░░░░░░ 0.12       │
└──────────────────────────────────────────┘
```

This is a **designed, intentional UI state** — not an error. The visual treatment makes it clear the system is being honest, not broken.

### 3.3 Graph Explorer UX

**First Impression**: The graph should immediately communicate "wow, this is a living knowledge map."

**Interaction Model**:

- **Default**: Show top 50 nodes by mention count
- **Click node**: Select → detail panel slides in from right
- **Hover node**: Tooltip with name + type + connection count
- **Double-click node**: Center + zoom in
- **Drag node**: Reposition (physics sim)
- **Scroll**: Zoom in/out
- **2D/3D toggle**: Prominent ToggleGroup at top
- **Background**: Subtle gradient background, not flat — creates depth

**Node Visual Rules**:

- Size: proportional to `mention_count` (min 6px, max 24px)
- Color: entity type (see Section 2 of DESIGN_SYSTEM.md)
- Glow effect: selected node gets CSS glow matching its color
- Label: show name when zoom level > 0.5, hide when zoomed out

**Edge Visual Rules**:

- Color: 20% opacity of source node color
- Width: 1px (thin, not overwhelming)
- Label: show relationship type on hover
- Direction: small arrowhead

### 3.4 Timeline View UX

**Design Model**: Think "Notion database with cards" — visual, scannable, filterable.

**Date Grouping**: Cards are grouped under sticky date headers: **"Today"**, **"Yesterday"**, **"Feb 12, 2026"**. This gives temporal context at a glance and makes the feed feel like a living journal rather than a flat list.

**Card Design**:

```
┌─────────────────────────────────────────┐
│ 📄 PDF   Strategy   Feb 12, 2026       │ ← modality icon + category badge + date
│                                         │
│ Q3 Budget Analysis Report               │ ← title (bold)
│                                         │
│ Summary of the quarterly budget with    │ ← summary (2-3 lines, truncated)
│ projections for Q4 spending...          │
│                                         │
│ 🔵 Sarah  🟢 Budget  🟡 Q3 Planning   │ ← entity chips (clickable)
│                                         │
│ ▸ 2 action items                        │ ← collapsible action items
└─────────────────────────────────────────┘
```

**Scroll behavior**: Virtualized infinite scroll (react-virtuoso) — renders only visible cards. Smooth even with 500+ items. Skeleton loading at bottom when fetching more.

**Empty state**: Custom Empty component — illustration of blank nodes + text "No memories yet. Synapsis is watching your directories and will populate this feed automatically."

### 3.5 Search UX

**Primary interaction**: Command palette (Cmd+K / Ctrl+K) — accessible from ANY view.

**Behavior**:

1. User presses `Cmd+K` → Command dialog opens with focused input
2. Type query → live results grouped by: Entities | Documents | Actions
3. Select result → navigate to relevant view (entity → Graph, document → Timeline card, action → view)
4. `Escape` → close

**Full search page**: `/search` route with filters — extended version of the command palette for detailed exploration.

### 3.6 Loading States Strategy

**Every async operation has a specific loading pattern**:

| Operation | Loading Pattern | Component |
|---|---|---|
| Chat answer | Skeleton (3 pulsing lines) → streaming text | Skeleton → text stream |
| Timeline load | Skeleton cards (3-5 card placeholders) | Skeleton |
| Graph load | Spinner centered on canvas + "Building your knowledge graph..." | Spinner + text |
| Source panel open | Skeleton for content area | Skeleton |
| Ingestion happening | Subtle progress bar at sidebar footer | Progress |
| Initial scan | Full-screen progress bar with file count | Progress + text |
| Command search | "Searching..." text in CommandEmpty | Spinner |

**Rule**: NEVER show a blank area while loading. Always show a purposeful loading state.

### 3.7 Error States Strategy

| Error | UX Treatment | Component |
|---|---|---|
| Ollama unreachable | Alert banner at top: "LLM service unavailable. Check if Ollama is running." | Alert (destructive) |
| Qdrant unreachable | Alert banner: "Vector store offline. Search may be limited." | Alert (destructive) |
| Query failed | Toast notification: "Failed to process your question. Please try again." | Sonner (error) |
| Ingestion failed (single file) | Toast: "Failed to process document.pdf — unsupported format" | Sonner (warning) |
| No results for query | Empty state inside chat: "I couldn't find anything relevant." | Empty |
| WebSocket disconnected | Small badge in sidebar: "Reconnecting..." with spinner | Badge + Spinner |

---

## 4. Micro-Copy Library

Consistent language across the entire application.

### 4.1 Navigation Labels

| View | Sidebar Label | Page Title |
|---|---|---|
| Chat | Chat | Ask Synapsis |
| Graph | Graph | Knowledge Graph |
| Timeline | Timeline | Memory Timeline |
| Search | Search | Search & Explore |
| Setup | Settings | Setup |

### 4.2 Chat Interface Copy

| Element | Text |
|---|---|
| Input placeholder | "Ask anything about your knowledge..." |
| Thinking state | "Thinking..." |
| Streaming indicator | (no text — just the cursor blinking at end of stream) |
| Empty chat | "Start a conversation. Ask about your notes, documents, or ideas." |
| Confidence: high | "High confidence" |
| Confidence: medium | "Medium confidence" |
| Confidence: low | "Low confidence" |
| Confidence: none | "Insufficient evidence" |
| Verification: APPROVE | "Verified" |
| Verification: REVISE | "Partially verified" |
| Verification: REJECT | "Unverified" |
| Abstention | "I don't have enough information in your records to answer this confidently." |
| Source panel title | "Supporting Evidence" |
| Reasoning toggle | "Why this answer?" |

### 4.3 Graph Interface Copy

| Element | Text |
|---|---|
| Empty graph | "Your knowledge graph will grow as Synapsis processes your files." |
| Node tooltip | "{name} — {type} — {connection_count} connections" |
| Detail panel title | "Entity Details" |
| No node selected | "Click a node to see its details and connections." |
| 2D/3D toggle labels | "2D" / "3D" |
| Filter placeholder | "Filter entities..." |

### 4.4 Timeline Interface Copy

| Element | Text |
|---|---|
| Empty timeline | "No memories yet. Drop files in your watched directories and they'll appear here automatically." |
| Filter: All | "All" |
| Filter labels | "Notes" / "PDFs" / "Images" / "Audio" / "JSON" |
| Loading more | "Loading more memories..." |
| Action items toggle | "{N} action items" |

### 4.5 Setup Wizard Copy

| Step | Heading | Subtext |
|---|---|---|
| Welcome | "Welcome to Synapsis" | "Your personal knowledge assistant. Synapsis silently watches your files and builds your knowledge graph — zero effort required." |
| Directories | "What should Synapsis watch?" | "Select the directories Synapsis will monitor. Files are read in read-only mode — we never modify your content." |
| Exclusions | "Anything to skip?" | "Optional: exclude file types or folders you don't want indexed." |
| Complete | "You're all set." | "Synapsis is now scanning your directories. Your knowledge graph will begin building in the background." |

### 4.6 System Notifications (Sonner Toasts)

| Event | Toast Text | Type |
|---|---|---|
| File ingested | "Processed: {filename}" | success |
| Batch complete | "{N} files processed successfully" | success |
| Connection found | "New connection: '{entity1}' linked to '{entity2}'" | info |
| Contradiction found | "Possible contradiction detected in '{topic}'" | warning |
| Ingestion error | "Failed to process: {filename}" | error |
| Health restored | "All services operational" | success |
| Service down | "{service} is unreachable" | error |

---

## 5. Demo Presentation UX

### 5.1 Demo Script Flow (for judges)

1. **Open browser** → Synapsis at localhost:3000
2. **Setup wizard** appears → Show directory selection (pre-populated, just click through)
3. **Initial scan starts** → Progress bar shows files being processed
4. **Navigate to Timeline** → Show knowledge cards appearing automatically
5. **Navigate to Graph** → "Wow moment" — Toggle to 3D, rotate the graph
6. **Go to Chat** → Ask the 5 pre-prepared queries
7. **Show source panel** → Click a citation, show evidence
8. **Show confidence** → Ask a question with low confidence → show graceful abstention

### 5.2 Pre-Loaded Demo State

For the demo, pre-ingest the 45-file dataset so:

- Timeline is already populated with rich knowledge cards
- Graph has ~50 nodes with visible clusters
- Chat has context to answer all 5 demo queries
- Setup wizard can be skipped (or shown briefly, then dismissed)

### 5.3 Demo Visual Priorities

| Priority | Element | Why |
|---|---|---|
| 1 | 3D Knowledge Graph (dark mode) | Judges remember visual "wow" moments. A glowing, interactive 3D graph is unforgettable. |
| 2 | Confidence badges + source citations | Demonstrates trust and transparency — exactly what judges value. |
| 3 | Zero-touch ingestion | "Watch — I didn't upload anything. It found everything automatically." |
| 4 | Graceful abstention | "Ask something it can't answer → shows 'I don't know' with partial results." |
| 5 | Speed | First token in <2s. Full answer in <8s. No loading spinners during demo queries (pre-cache if needed). |

---

## 6. Competitive Visual Differentiation

### 6.1 What Other Hackathon Projects Look Like

| Common pattern | Synapsis difference |
|---|---|
| White background, basic bootstrap/tailwind | **Dark mode, sophisticated shadcn/ui components** |
| Simple chat bubble interface | **Chat + citations + confidence + reasoning collapsible** |
| No data visualization | **Interactive 2D/3D knowledge graph** |
| Upload button | **No upload button — zero-touch** |
| "Loading..." text | **Beautiful skeleton + spinner states** |
| Basic color scheme | **Deliberate semantic color system (confidence, entities, verification)** |
| No empty states | **Custom Empty components with helpful messaging** |
| No error handling UX | **Graceful alerts, toasts, and abstention UI** |
| No accessibility | **ARIA combobox, dialog focus traps, keyboard nav, live regions** |

### 6.2 Visual Signature Elements (What makes Synapsis instantly recognizable)

1. **The Graph**: Glowing colored nodes on dark canvas = the hero image of the project
2. **Confidence System**: Green/amber/orange/gray badges are unique to us — no other RAG project shows this
3. **Source Citations**: `[Source 1]` badges with hover previews — looks polished and academic
4. **Dark sidebar**: Always-present navigation with ingestion status = feels like a professional tool
5. **Typography contrast**: Geist Sans for UI + Geist Mono for data = clear information hierarchy

---

## 7. Brand Assets Checklist

| Asset | Status | Notes |
|---|---|---|
| Logo (SVG, icon + wordmark) | To create | Two connected nodes + "SYNAPSIS" |
| Favicon (ico + png) | To create | Icon-only version, 16x16, 32x32, 192x192 |
| OG Image (1200x630) | To create | For link previews if shared |
| Color tokens CSS | In DESIGN_SYSTEM.md | All oklch values defined |
| Font files | Pre-loaded via Next.js | Geist Sans + Geist Mono |
| Icon set | Lucide React | Pre-installed with shadcn/ui |
| Loading animation | To create | Two nodes connecting animation (CSS) |
| Empty state illustrations | Optional | Can use Lucide icons as illustrations |

---

## 8. Implementation Priorities

| Priority | Item | Impact |
|---|---|---|
| P0 | Dark/light mode with CSS variables | Foundation for all visual work |
| P0 | Sidebar navigation shell | Core layout — every view lives inside this |
| P0 | Chat View with confidence badges | Primary interaction surface |
| P0 | Graph Explorer with 3D | Demo wow factor |
| P0 | Timeline with knowledge cards | Shows persistent memory |
| P0 | Setup Wizard | First-run experience |
| P1 | Command palette (Cmd+K) | Power user feature, impressive in demo |
| P1 | Loading/error/empty states | Polish that signals quality |
| P1 | Toast notifications for ingestion | Shows real-time system activity |
| P1 | Source panel with evidence | Proves grounding and trust |
| P2 | Animations and transitions | Delight |
| P2 | Full search page | Extended functionality |
| P2 | Ingestion status dashboard | Secondary monitoring feature |
