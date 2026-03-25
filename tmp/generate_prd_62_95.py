#!/usr/bin/env python3
"""Generate tasks for groups 62-95 (UX Polish + Infrastructure + Security + Testing + Docs + Stretch)."""
import json

NEW_TASKS = []

def t(group, title, desc):
    NEW_TASKS.append({"title": title, "completed": False, "parallel_group": group, "description": desc})

# ═══════════════════════════════════════════════════════
# GROUP 62: Micro-Animations (10 tasks)
# ═══════════════════════════════════════════════════════
t(62, "Create animation utility library",
  "Create frontend/src/lib/animations.js — shared animation utilities using CSS transitions and Web Animations API. "
  "Exports: fadeIn(el, duration), fadeOut(el, duration), slideIn(el, direction, duration), "
  "slideOut(el, direction, duration), scaleIn(el), bounceIn(el), staggerChildren(parent, delay). "
  "Also create frontend/src/assets/animations.css with reusable CSS animation classes: "
  ".animate-fade-in, .animate-slide-up, .animate-scale-in, .animate-bounce. "
  "Use CSS custom properties for configurable duration and delay. "
  "Respect prefers-reduced-motion media query — disable animations for accessibility.")

t(62, "Add page transition animations",
  "Update frontend/src/App.vue to add smooth transitions between route changes. "
  "Use Vue's <Transition> component wrapping <RouterView>. "
  "Transition type: slide-fade (content slides slightly left and fades as new page slides in from right). "
  "Duration: 200ms. Easing: ease-out. "
  "Add CSS in frontend/src/assets/animations.css: "
  ".page-enter-active, .page-leave-active { transition: all 0.2s ease-out; } "
  ".page-enter-from { opacity: 0; transform: translateX(20px); } "
  ".page-leave-to { opacity: 0; transform: translateX(-20px); }")

t(62, "Add card hover and interaction animations",
  "Update all card components (AccountCard, TemplateCard, PersonaCard, KPI cards, etc.) with: "
  "Hover: subtle shadow increase and 1px lift (translateY(-1px)), 150ms transition. "
  "Click: brief scale down to 0.98 then back to 1.0 (tactile feedback). "
  "Focus: visible focus ring with brand blue color. "
  "Create a shared CSS class .card-interactive that can be applied to any card. "
  "Add to frontend/src/assets/animations.css. "
  "Ensure transitions are smooth and not jarring. Test on existing card components.")

t(62, "Add loading skeleton components",
  "Create frontend/src/components/common/Skeleton.vue — skeleton loading placeholder. "
  "Variants: SkeletonText (rectangular pulse), SkeletonCircle (circular), SkeletonCard (card-shaped). "
  "Props: width, height, variant, lines (for text variant). "
  "Shimmer animation: gradient that slides from left to right (CSS animation). "
  "Use throughout the app: replace loading spinners in data-heavy components. "
  "Create SkeletonKpiRow, SkeletonTable, SkeletonChart presets for common layouts. "
  "Use gray/light-gray color scheme matching the component being loaded.")

t(62, "Add list item stagger animations",
  "Update list and grid components to stagger item appearance on mount. "
  "When data loads, items appear one after another with 50ms delay between each. "
  "Use Vue's <TransitionGroup> with stagger delay computed from index. "
  "Apply to: AccountCard grids, TemplateGallery, activity feed items, table rows. "
  "Animation: fade-in + slide-up, 200ms duration per item. "
  "Max stagger 10 items (after that, all appear together to avoid long waits). "
  "Use the staggerChildren utility from animations.js.")

t(62, "Add chart entrance animations",
  "Update all D3.js chart components to animate on mount: "
  "Bar charts: bars grow from zero to full height. "
  "Line charts: line draws from left to right (using stroke-dasharray animation). "
  "Donut/pie charts: arcs grow from center (0 radius to full). "
  "Area charts: area fills from bottom up. "
  "Gauges: needle sweeps from left to current value. "
  "Duration: 800ms with ease-out easing. "
  "Only animate on first mount, not on data updates (data updates should transition smoothly). "
  "Update chartUtils.js with shared animation helper functions.")

t(62, "Add button and form interaction animations",
  "Update button components and form elements with micro-interactions: "
  "Button click: brief ripple effect (CSS radial gradient animation from click point). "
  "Form field focus: border color transition to brand blue, subtle glow. "
  "Checkbox/toggle: smooth check mark animation (CSS path animation). "
  "Dropdown open: slide-down with fade. "
  "Submit button loading: text transitions to spinner then to success check. "
  "Error state: brief shake animation on invalid fields. "
  "Create shared classes in animations.css.")

t(62, "Add number count-up animations",
  "Ensure all KPI cards and stat displays use the AnimatedCounter component (from group 35). "
  "If AnimatedCounter doesn't exist yet, create a simpler version: "
  "Vue composable useCountUp(targetValue, duration) that returns an animated ref. "
  "Uses requestAnimationFrame with easing function. "
  "Apply to: all KPI card values, dashboard stats, chart labels with large numbers. "
  "Numbers should count up when the component mounts or when the value changes. "
  "Use the existing useCountUp.js composable if it has this functionality already.")

t(62, "Add notification and toast animations",
  "Update NotificationToast and GlobalActivityFeed with smooth animations: "
  "Toast entrance: slide in from right with spring easing. "
  "Toast exit: fade out and collapse height. "
  "Activity feed: new items slide in from top with stagger. "
  "Badge count update: scale bump animation on the count number. "
  "Bell icon: subtle shake when new notifications arrive. "
  "Use CSS @keyframes for these animations.")

t(62, "Add modal and panel transition animations",
  "Update all modals, slide-overs, and panels with smooth open/close transitions: "
  "Modal: backdrop fades in (0 to 0.5 opacity), modal scales from 0.95 to 1.0 with fade. "
  "Slide-over: slides in from right edge, push/overlay modes. "
  "Dropdown: scale from top-left anchor point with fade. "
  "Close animations reverse the opening. Duration: 200ms. "
  "Use Vue <Transition> with CSS classes. "
  "Ensure keyboard navigation (Escape to close) works during animations.")

# ═══════════════════════════════════════════════════════
# GROUP 63: Keyboard Shortcuts System (8 tasks)
# ═══════════════════════════════════════════════════════
t(63, "Create keyboard shortcuts composable",
  "Create frontend/src/composables/useKeyboardShortcuts.js — centralized keyboard shortcut manager. "
  "KeyboardShortcutManager: singleton that registers and handles global keyboard shortcuts. "
  "register(shortcut, handler, options): shortcut is a string like 'ctrl+k', 'shift+n', 'escape'. "
  "unregister(shortcut): remove a shortcut. "
  "Options: { scope: 'global'|'page', description: string, category: string }. "
  "Handle modifier keys: ctrl/cmd (platform-aware), shift, alt. "
  "Prevent conflicts: warn if a shortcut is already registered. "
  "Disable shortcuts when user is typing in an input/textarea. "
  "Provide/inject pattern for component-level shortcuts.")

t(63, "Register global keyboard shortcuts",
  "Using the keyboard shortcuts composable, register these global shortcuts: "
  "Ctrl/Cmd+K: Open command palette. "
  "Ctrl/Cmd+N: Create new simulation. "
  "Ctrl/Cmd+S: Save current work (dashboard, report, etc.). "
  "Escape: Close modal/panel/palette. "
  "/: Focus search/filter input on current page. "
  "?: Open keyboard shortcuts help modal. "
  "G then D: Go to Dashboard. G then S: Go to Simulations. G then R: Go to Reports. "
  "Register in App.vue or main layout component. "
  "Ensure all shortcuts work across all pages.")

t(63, "Register simulation-specific shortcuts",
  "Register shortcuts when in simulation workspace: "
  "Space: Play/Pause simulation or replay. "
  "Left Arrow: Previous round. Right Arrow: Next round. "
  "+/-: Increase/decrease playback speed. "
  "T: Toggle transparency mode (show agent thinking). "
  "M: Toggle metrics panel. "
  "F: Toggle full-screen mode. "
  "B: Create branch at current round. "
  "Unregister these shortcuts when leaving simulation workspace.")

t(63, "Build keyboard shortcuts help modal",
  "Create frontend/src/components/common/KeyboardShortcutsHelp.vue — modal showing all available shortcuts. "
  "Opens with '?' key. "
  "Organized by category: Global, Navigation, Simulation, Report Builder, Dashboard. "
  "Each shortcut: key combination (styled as keyboard keys), description. "
  "Platform-aware: show Cmd on macOS, Ctrl on Windows/Linux. "
  "Searchable: filter shortcuts by description. "
  "Clean two-column layout. Close with Escape or clicking X.")

t(63, "Add navigation shortcuts",
  "Register navigation shortcuts using G (go) prefix: "
  "G then D: Go to GTM Dashboard. G then P: Go to Pipeline. G then R: Go to Revenue. "
  "G then O: Go to Orders. G then C: Go to CPQ. G then A: Go to Analytics. "
  "G then S: Go to Simulations. G then T: Go to Scenario Templates. "
  "G then N: Go to Agent Management. "
  "Implementation: on G press, wait 500ms for second key. If no second key, ignore. "
  "Show visual indicator when in 'G mode' (waiting for second key).")

t(63, "Add dashboard builder shortcuts",
  "Register shortcuts when in dashboard builder: "
  "E: Toggle edit mode. "
  "Delete/Backspace: Delete selected widget. "
  "Ctrl/Cmd+Z: Undo last action. Ctrl/Cmd+Shift+Z: Redo. "
  "Ctrl/Cmd+D: Duplicate selected widget. "
  "Arrow keys: move selected widget by one grid unit. "
  "These only active when DashboardBuilderView is mounted.")

t(63, "Add report builder shortcuts",
  "Register shortcuts when in report builder: "
  "Ctrl/Cmd+P: Preview report. "
  "Ctrl/Cmd+E: Export report. "
  "Ctrl/Cmd+Shift+S: Save as new template. "
  "Delete: Remove selected section. "
  "Ctrl/Cmd+Up/Down: Move section up/down. "
  "These only active when ReportBuilderView is mounted.")

t(63, "Build shortcut indicator badges",
  "Add keyboard shortcut hint badges to UI elements throughout the app: "
  "Buttons with shortcuts: show shortcut as a small badge (e.g., 'Search' button shows 'Ctrl+K'). "
  "Nav items: show navigation shortcut on hover tooltip. "
  "Sidebar items: show shortcuts in tooltips. "
  "Command palette actions: show shortcuts next to action names. "
  "Use a small, subtle font for shortcut hints. Only show on desktop (hide on mobile/touch). "
  "Platform-aware: Cmd on Mac, Ctrl on Windows.")

# ═══════════════════════════════════════════════════════
# GROUP 64: Drag-and-Drop Reordering (8 tasks)
# ═══════════════════════════════════════════════════════
t(64, "Create drag-and-drop composable",
  "Create frontend/src/composables/useDragAndDrop.js — generic drag-and-drop functionality. "
  "Uses HTML5 Drag and Drop API (or install a small library like @vueuse/core which has useDraggable). "
  "Exports: useDragSource(el, data), useDropTarget(el, onDrop), useSortable(list, onReorder). "
  "useSortable: takes a reactive array, returns sorted array and handlers. "
  "Visual feedback: dragged item becomes semi-transparent, drop zone highlights on dragover. "
  "Touch support: use touch events as fallback for mobile. "
  "Drop zone validation: optionally specify which data types a target accepts.")

t(64, "Add drag-and-drop to dashboard widgets",
  "Update DashboardGrid.vue to use the drag-and-drop composable. "
  "Widgets can be dragged by their header/drag handle. "
  "Grid cells highlight valid drop positions. "
  "Show widget ghost (outline) at the target position while dragging. "
  "Snap to grid on drop. Animate widget sliding to new position. "
  "Prevent overlapping: displaced widgets move out of the way. "
  "Save new layout to store after reorder.")

t(64, "Add drag-and-drop to report builder sections",
  "Update ReportCanvas.vue to support section reordering via drag-and-drop. "
  "Drag handle on each section (left side grab icon). "
  "Blue drop indicator line between sections showing where the dragged section will go. "
  "Animate sections sliding apart to make room. "
  "Support dragging from SectionPalette to canvas (new section). "
  "Support dragging within canvas (reorder). "
  "Support dragging out of canvas to remove (with confirmation).")

t(64, "Add drag-and-drop to team composer",
  "Update TeamComposer.vue to use drag-and-drop for building simulation teams. "
  "Drag PersonaCards from the available pool to team slots. "
  "Drag between team slots to reorder. "
  "Drag off the team area to remove from team. "
  "Visual feedback: empty slots pulse when a card is being dragged. "
  "Reject animation: card bounces back if team is full or role conflicts.")

t(64, "Add sortable tables with drag-and-drop",
  "Create frontend/src/components/common/SortableTable.vue — table with draggable row reordering. "
  "Drag handle column on the left (grip icon). "
  "Dragging a row shows the row as a floating element following cursor. "
  "Drop indicator: blue line between rows showing target position. "
  "Emit 'reorder' event with new order. "
  "Use for: scenario priority ordering, agent team ordering, report section ordering. "
  "Keyboard alternative: Ctrl+Up/Down to reorder selected row.")

t(64, "Add drag-and-drop to navigation items",
  "Update AppNav.vue to support user-reorderable navigation items. "
  "In edit mode (toggle via a customize button), nav items become draggable. "
  "Drag to reorder. Drop indicator between items. "
  "Save custom order to localStorage. "
  "Reset button to restore default order. "
  "Add ability to hide/show nav items (toggle visibility). "
  "This is a nice-to-have polish feature for power users.")

t(64, "Add drag-and-drop to widget picker",
  "Update WidgetPicker.vue so widgets can be dragged directly from the picker onto the dashboard grid. "
  "Widget card in picker becomes a drag source. "
  "Dashboard grid becomes a drop target. "
  "Ghost preview shows approximate widget size during drag. "
  "On drop: create widget at the drop position with default configuration. "
  "Auto-open widget config panel after drop.")

t(64, "Add drag-and-drop visual polish",
  "Polish all drag-and-drop interactions across the app: "
  "Consistent cursor: 'grab' on hover, 'grabbing' while dragging. "
  "Drag ghost: semi-transparent clone of the dragged element. "
  "Drop zone highlights: subtle blue glow on valid targets. "
  "Invalid drop zone: red tint and 'not-allowed' cursor. "
  "Animation: smooth transition when items settle into new positions. "
  "Accessibility: all drag-and-drop actions also achievable via keyboard.")

# ═══════════════════════════════════════════════════════
# GROUP 65: Rich Text Editor (8 tasks)
# ═══════════════════════════════════════════════════════
t(65, "Install and configure rich text editor",
  "Install a lightweight rich text editor library for Vue 3. Options: tiptap (recommended), or milkdown. "
  "Run: cd frontend && pnpm add @tiptap/vue-3 @tiptap/starter-kit @tiptap/extension-placeholder. "
  "Create frontend/src/components/common/RichTextEditor.vue — wrapper component. "
  "Props: modelValue (HTML or Markdown string), placeholder, minHeight, maxHeight, toolbar (which buttons). "
  "Emit: update:modelValue on content change. "
  "Basic configuration: paragraph, headings (H1-H3), bold, italic, bullet list, ordered list, code block.")

t(65, "Build editor toolbar component",
  "Create frontend/src/components/common/EditorToolbar.vue — toolbar for the rich text editor. "
  "Buttons: Bold (B), Italic (I), Heading 1/2/3, Bullet List, Ordered List, "
  "Code Block, Link, Divider, Undo, Redo. "
  "Active state: button highlighted when cursor is in that format. "
  "Tooltip on each button with keyboard shortcut hint. "
  "Clean design: subtle gray background, small icon buttons, dividers between groups. "
  "Match Intercom UI style. Use Heroicons or similar for icons.")

t(65, "Add rich text editor to scenario descriptions",
  "Update ScenarioBuilderView.vue to use RichTextEditor for scenario descriptions. "
  "Replace plain text textarea with the rich text editor. "
  "Support: headings for section titles, bold for emphasis, bullet lists for objectives. "
  "Store content as HTML string in scenario config. "
  "Render stored HTML in read-only scenarios (TemplateDetail, etc.). "
  "Character count indicator below editor.")

t(65, "Add rich text editor to report text sections",
  "Update TextSectionEditor.vue in the report builder to use RichTextEditor. "
  "Support full formatting: headings, bold, italic, lists, code blocks. "
  "Add: blockquote style for callout/highlight sections. "
  "Preview mode renders the formatted text. "
  "Export respects formatting (Markdown export converts HTML to Markdown).")

t(65, "Add rich text editor to agent backstories",
  "Update AgentWizardBasic.vue to use RichTextEditor for agent backstory field. "
  "Support: basic formatting (bold, italic, bullets). "
  "Character limit: 500 characters (show counter). "
  "Placeholder text: 'Describe this agent\\'s background, experience, and perspective...' "
  "Render formatted backstory in PersonaCard expanded view.")

t(65, "Add rich text editor to annotations and notes",
  "Update TimelineAnnotations.vue to use RichTextEditor for annotation text. "
  "Compact editor: fewer toolbar options (bold, italic, bullet only). "
  "Also update resolution notes in ResolutionWorkflow.vue. "
  "And report builder text sections. "
  "Consistent editing experience across all text input areas that support formatting.")

t(65, "Add Markdown import/export to editor",
  "Add Markdown support to RichTextEditor: "
  "Import: accept Markdown string as modelValue and convert to editor format. "
  "Export: provide method to get content as Markdown string. "
  "Use a lightweight conversion library (turndown for HTML→MD, or tiptap's built-in). "
  "Toggle button: switch between WYSIWYG and Markdown source view. "
  "Markdown source view: monospace textarea with syntax highlighting (optional).")

t(65, "Add auto-save to editor instances",
  "Create frontend/src/composables/useAutoSave.js — auto-saves editor content to localStorage. "
  "Debounced save: save to localStorage 2 seconds after last change. "
  "Recovery: on mount, check localStorage for unsaved content. Show recovery banner: "
  "'Unsaved changes found from [time]. Restore or Discard?' "
  "Apply to: scenario descriptions, agent backstories, report text sections, annotations. "
  "Clear saved content after successful manual save. "
  "Unique key per editor instance based on entity ID.")

# ═══════════════════════════════════════════════════════
# GROUP 66: CHECKPOINT (1 task)
# ═══════════════════════════════════════════════════════
t(66, "CHECKPOINT: Verify app builds and runs after UX polish features",
  "Run comprehensive build and smoke test: "
  "1) cd frontend && pnpm install && pnpm build — verify no build errors from new dependencies (tiptap, etc.). "
  "2) cd frontend && pnpm lint — verify no linting errors. "
  "3) Verify animations respect prefers-reduced-motion. "
  "4) Verify keyboard shortcuts don't conflict with browser defaults. "
  "5) Test keyboard shortcuts: ?, Ctrl+K, G+D, Space (in simulation). "
  "6) Verify drag-and-drop works (no JS errors in console). "
  "7) Verify rich text editor renders and saves content. "
  "8) Count total new npm packages added. "
  "9) Check bundle size hasn't grown excessively: cd frontend && pnpm build && du -sh dist/. "
  "10) Verify all existing features still work (no regressions from animation/interaction changes). "
  "Fix issues. Create docs/checkpoint-group-66.md.")

# ═══════════════════════════════════════════════════════
# GROUP 67: Custom Theming Engine (8 tasks)
# ═══════════════════════════════════════════════════════
t(67, "Create theme data model and defaults",
  "Create frontend/src/lib/themes.js — theme definitions and management. "
  "Theme interface: { name, colors: {primary, secondary, accent, background, surface, text, error, success, warning}, "
  "fonts: {heading, body, mono}, borderRadius: {sm, md, lg}, shadows: {sm, md, lg} }. "
  "Default themes: 'Intercom' (blue primary, brand colors), 'Dark' (dark backgrounds, light text), "
  "'Corporate' (navy primary, serif headings), 'Minimal' (gray tones, no shadows). "
  "Store active theme in Pinia settings store. Apply via CSS custom properties on :root. "
  "Persist selection to localStorage.")

t(67, "Build theme switcher component",
  "Create frontend/src/components/settings/ThemeSwitcher.vue — UI for switching themes. "
  "Grid of theme preview cards: small rectangle showing the theme's primary colors and sample text. "
  "Click to apply. Current theme highlighted with a checkmark. "
  "Live preview: theme applies immediately on hover (debounced). "
  "Add to SettingsView.vue in an 'Appearance' section. "
  "Smooth transition when switching themes (fade colors over 300ms).")

t(67, "Build custom theme editor component",
  "Create frontend/src/components/settings/ThemeEditor.vue — create custom themes. "
  "Color pickers for each theme color (primary, secondary, accent, etc.). "
  "Font family selectors for heading and body fonts (dropdown with preview). "
  "Border radius slider (small to large). Shadow intensity slider. "
  "Live preview panel showing a miniature dashboard with current custom settings. "
  "Save custom theme with a name. Edit existing custom themes. "
  "Reset to default button. Import/Export theme as JSON.")

t(67, "Implement CSS custom properties theming",
  "Update frontend/src/assets/brand-tokens.css to use CSS custom properties for all design tokens. "
  "Replace hardcoded colors with var(--color-primary), var(--color-background), etc. "
  "Update Tailwind config to use CSS custom properties where possible. "
  "Create frontend/src/lib/applyTheme.js — function that sets CSS custom properties on :root based on theme object. "
  "Call on app mount and when theme changes. "
  "Ensure all components use the custom properties instead of hardcoded values.")

t(67, "Update all components to use theme tokens",
  "Audit and update components to ensure they use CSS custom properties: "
  "Buttons: background, text color, hover state from theme tokens. "
  "Cards: background, border, shadow from theme tokens. "
  "Charts: brand color palette from theme tokens (update chartUtils.js). "
  "Text: heading and body font families from theme tokens. "
  "Focus on high-visibility components: nav bar, KPI cards, chart backgrounds, button styles. "
  "Don't need to update every single component — focus on the ones visible in a demo walkthrough.")

t(67, "Implement dark mode theme",
  "Ensure the 'Dark' theme works correctly across all components. "
  "Dark mode colors: background #1a1a1a, surface #2d2d2d, text #f0f0f0, primary #4d8cff (lighter blue). "
  "Check all D3 charts render correctly on dark backgrounds. "
  "Check all text is readable. Check all borders and dividers are visible. "
  "Check code blocks and editors have dark variants. "
  "Check loading skeletons use dark colors. "
  "Use useTheme.js composable (if exists) or create one for dark mode detection.")

t(67, "Build theme-aware chart colors",
  "Update frontend/src/lib/chartUtils.js to provide theme-aware color palettes. "
  "Export getChartColors() that reads current theme and returns appropriate chart colors. "
  "Light themes: use darker, saturated colors on white backgrounds. "
  "Dark themes: use lighter, slightly desaturated colors on dark backgrounds. "
  "Ensure sufficient contrast ratio for accessibility (WCAG AA). "
  "Update all D3 chart components to call getChartColors() instead of hardcoded palettes.")

t(67, "Add theme persistence and system preference detection",
  "Update the theme system to: "
  "1) Persist selected theme to localStorage. "
  "2) On first visit, detect system preference: window.matchMedia('(prefers-color-scheme: dark)'). "
  "3) Auto-apply dark/light based on system preference if no user selection. "
  "4) Listen for system preference changes (mediaQuery change event) and update if 'Auto' selected. "
  "Add 'Auto' option in ThemeSwitcher that follows system preference. "
  "Add to Settings page: 'Theme follows system preference' toggle.")

# ═══════════════════════════════════════════════════════
# GROUP 68: WebSocket Real-Time Updates (8 tasks)
# ═══════════════════════════════════════════════════════
t(68, "Set up Flask-SocketIO backend",
  "Install flask-socketio and required async library: add to backend/requirements.txt. "
  "Update backend/app/__init__.py to create SocketIO instance: socketio = SocketIO(app, cors_allowed_origins='*'). "
  "Update backend/run.py to use socketio.run(app) instead of app.run(). "
  "Verify WebSocket connection works: create a simple 'ping' event handler. "
  "Configure logging for WebSocket events. "
  "Handle WebSocket connection errors gracefully.")

t(68, "Create real-time event emitter service",
  "Create backend/app/services/realtime_emitter.py — centralized event emission for real-time updates. "
  "EventEmitter class (singleton): "
  "emit(event_type, data, room=None): emits event to connected clients. "
  "Event types: simulation_update, data_refresh, notification, activity_event, system_status. "
  "Room-based: simulations use simulation_id as room. Global events broadcast to all. "
  "Call from: simulation engine (round updates), data generators (refresh events), activity feed. "
  "Rate limit: max 10 events per second per event type to prevent flooding.")

t(68, "Create WebSocket event handlers",
  "Create backend/app/api/websocket_handlers.py — SocketIO event handlers. "
  "Events: "
  "@socketio.on('connect'): log connection, add to global room. "
  "@socketio.on('disconnect'): log, cleanup. "
  "@socketio.on('join_simulation'): add client to simulation room. "
  "@socketio.on('leave_simulation'): remove from simulation room. "
  "@socketio.on('subscribe_data'): subscribe to data type updates (revenue, pipeline, etc.). "
  "@socketio.on('request_refresh'): trigger data refresh and emit update. "
  "Register handlers in the app factory.")

t(68, "Update frontend WebSocket composable",
  "Update frontend/src/composables/useWebSocket.js (if exists) or create it: "
  "Install socket.io-client: cd frontend && pnpm add socket.io-client. "
  "Composable: connect(), disconnect(), joinSimulation(id), leaveSimulation(id), "
  "subscribeData(type), on(event, handler), emit(event, data). "
  "Auto-reconnect with exponential backoff (1s, 2s, 4s, max 30s). "
  "Connection status: connected, reconnecting, disconnected (reactive refs). "
  "Clean up all listeners on component unmount.")

t(68, "Connect simulation to WebSocket updates",
  "Update SimulationWorkspaceView.vue and LiveFeed.vue to use WebSocket: "
  "On simulation start: joinSimulation(id). "
  "Listen for 'round_complete' events: update round data. "
  "Listen for 'agent_message' events: append to message feed. "
  "Listen for 'metric_update' events: update chart data. "
  "Listen for 'simulation_status' events: update controls. "
  "On leave: leaveSimulation(id). "
  "Fallback: if WebSocket fails, fall back to polling (GET /api/simulation/<id>/status every 3s).")

t(68, "Connect data views to WebSocket updates",
  "Update Pinia stores to accept WebSocket-pushed data updates: "
  "Revenue store: listen for 'revenue_update' → refresh metrics. "
  "Pipeline store: listen for 'pipeline_update' → refresh funnel data. "
  "Activity feed: listen for 'activity_event' → prepend to feed. "
  "Notification: listen for 'notification' → show toast. "
  "Add 'Auto-refresh' toggle in data views — when on, accept WebSocket pushes. "
  "Show 'Last updated X seconds ago' with live counter.")

t(68, "Build WebSocket connection status indicator",
  "Update SystemStatusBar.vue to show WebSocket connection status: "
  "Green dot + 'Connected' when WebSocket is connected. "
  "Yellow dot + 'Reconnecting...' when reconnecting (with attempt count). "
  "Red dot + 'Disconnected' when connection lost. "
  "Click to manually reconnect. "
  "Show latency: measure round-trip time of ping/pong. Display in ms. "
  "Also show in the ServiceStatus component on settings page.")

t(68, "Add WebSocket authentication",
  "Update WebSocket connection to include auth context: "
  "On connect: send session token or API key as auth parameter. "
  "Backend: validate auth on connection. Reject unauthorized connections. "
  "For demo mode (no auth): accept all connections. "
  "For auth mode: verify token from cookie or query parameter. "
  "Add namespace separation: /simulation, /data, /notifications. "
  "Each namespace can have different auth requirements.")

# ═══════════════════════════════════════════════════════
# GROUP 69: Service Worker + Offline (8 tasks)
# ═══════════════════════════════════════════════════════
t(69, "Create service worker for caching",
  "Create frontend/public/sw.js — service worker for offline asset caching. "
  "Cache strategy: Cache-first for static assets (JS, CSS, images, fonts). "
  "Network-first for API calls (try network, fall back to cached response). "
  "Pre-cache: index.html, main CSS/JS bundles, brand assets (logo, icons). "
  "Update strategy: when new version detected, notify user with 'Update available' banner. "
  "Register service worker in frontend/src/main.js: if ('serviceWorker' in navigator) { ... }. "
  "Only register in production build (not in dev mode).")

t(69, "Implement IndexedDB data store",
  "Create frontend/src/lib/offlineStore.js — IndexedDB wrapper for offline data persistence. "
  "Uses the idb library (install: cd frontend && pnpm add idb). "
  "Stores: simulations, dashboards, reports, settings, recentData. "
  "API: getAll(store), get(store, key), put(store, key, data), delete(store, key), clear(store). "
  "Auto-save data fetched from API to IndexedDB. "
  "On offline: return data from IndexedDB instead of failing. "
  "Storage limit management: max 50MB, LRU eviction for old data.")

t(69, "Build offline mode detection composable",
  "Create frontend/src/composables/useOfflineMode.js — detects and manages offline state. "
  "Reactive refs: isOnline (boolean), connectionType (string), lastOnline (Date). "
  "Uses navigator.onLine and 'online'/'offline' events. "
  "Also implements connectivity check: periodic fetch to /api/health (every 30s when online). "
  "Provide/inject for app-wide access. "
  "When offline → switch all data fetching to IndexedDB. "
  "When back online → sync queued changes and refresh data.")

t(69, "Build offline banner component",
  "Create frontend/src/components/common/OfflineBanner.vue — shows when app is offline. "
  "Yellow banner at top of page: 'You are currently offline. Data may not be up to date.' "
  "Animate in when going offline, out when coming back online. "
  "Show 'Last synced: X minutes ago'. "
  "Show 'Reconnecting...' with spinner when trying to reconnect. "
  "Show 'Back online! Syncing...' with green check when reconnected. "
  "Dismissible: user can close but it returns if still offline.")

t(69, "Update Pinia stores for offline support",
  "Update key Pinia stores to support offline data: "
  "On fetch: try API, fall back to IndexedDB. "
  "On successful API fetch: save to IndexedDB for offline use. "
  "On offline: serve from IndexedDB, add 'offline' flag to data. "
  "Stores to update: settings, dashboards, simulation results, report templates. "
  "Add isOfflineData computed property so UI can indicate stale data. "
  "Queued writes: if user makes changes offline, queue for sync when back online.")

t(69, "Implement background sync for queued changes",
  "Create frontend/src/lib/syncQueue.js — queues changes made offline for later sync. "
  "Queue: array of { endpoint, method, body, timestamp } stored in IndexedDB. "
  "When back online: process queue in order, handle conflicts. "
  "Conflict resolution: server wins (user notified if their change was overridden). "
  "Show sync progress: 'Syncing 3 queued changes...' in OfflineBanner. "
  "Max queue size: 100 items. Warn user when approaching limit. "
  "Clear queue on successful sync.")

t(69, "Cache simulation results for offline replay",
  "Update simulation stores to cache completed simulation results in IndexedDB. "
  "Cache: full simulation results (all rounds, interactions, metrics). "
  "Allow offline replay of cached simulations. "
  "Show 'Cached' badge on simulation list items that are available offline. "
  "Cache management: keep last 10 simulations, evict oldest when at limit. "
  "Settings page: 'Manage Offline Cache' showing size and cached items. Clear cache button.")

t(69, "Add offline-first report viewing",
  "Cache generated reports in IndexedDB for offline viewing. "
  "Report list: show offline-available reports with a cached indicator. "
  "Viewing cached report: full content and charts render from cached data. "
  "Charts that require live data: show 'Offline — data from [date]' watermark. "
  "Allow offline report builder access with cached data. "
  "Sync new report data when back online.")

# ═══════════════════════════════════════════════════════
# GROUP 70: API Caching + Lazy Loading (8 tasks)
# ═══════════════════════════════════════════════════════
t(70, "Implement API response caching",
  "Create frontend/src/lib/apiCache.js — in-memory cache for API responses. "
  "Cache: Map<url+params, {data, timestamp, ttl}>. "
  "get(key): return cached data if within TTL, null otherwise. "
  "set(key, data, ttl): store with TTL (default 60 seconds). "
  "invalidate(pattern): clear matching keys (e.g., '/api/revenue/*'). "
  "invalidateAll(): clear entire cache. "
  "Update frontend/src/api/client.js to check cache before making requests. "
  "TTL by endpoint type: static data (5min), dynamic data (30s), user data (10s).")

t(70, "Implement route-based code splitting",
  "Update frontend/src/router/index.js to use dynamic imports for all route components. "
  "Change: import SalesforceView from '...' → component: () => import('../views/SalesforceView.vue'). "
  "Apply to all views: SalesforceView, CpqView, PipelineView, RevenueView, OrdersView, "
  "ReconciliationView, GtmDashboardView, DataPipelineView, SimulationWorkspaceView, "
  "ReportBuilderView, AnalyticsView, CampaignsView, AgentsView, etc. "
  "This creates separate JS chunks that load on demand. "
  "Add loading component: show a loading indicator while the chunk loads. "
  "Preload critical routes: prefetch dashboard and simulation views on app mount.")

t(70, "Implement component lazy loading",
  "Use Vue's defineAsyncComponent for heavy components that aren't immediately visible: "
  "Chart components: load D3 charts only when they're in the viewport. "
  "Modal/panel components: load only when opened. "
  "Rich text editor: load only when user clicks edit. "
  "Use IntersectionObserver to trigger lazy loading: load when component is within 200px of viewport. "
  "Show skeleton placeholders while components load. "
  "Prioritize above-the-fold content loading.")

t(70, "Implement image and asset lazy loading",
  "Add lazy loading to all images and heavy assets: "
  "Images: loading='lazy' attribute on all <img> tags. "
  "D3 visualizations: only initialize when visible (IntersectionObserver). "
  "Agent avatars: generate once and cache in memory. "
  "Chart libraries: import D3 modules individually (d3-scale, d3-axis, etc.) instead of full d3 bundle. "
  "Font loading: font-display: swap for custom fonts to prevent FOIT.")

t(70, "Add data pagination to large lists",
  "Update all list/table components that could have large datasets to use pagination: "
  "Default: 20 items per page. Show: 10, 20, 50, 100 options. "
  "Server-side pagination: pass page/per_page to backend, return total count. "
  "Client-side pagination for small datasets (<100 items). "
  "Virtual scrolling for very large lists (>100 visible items): use vue-virtual-scroller or implement. "
  "Apply to: simulation list, report list, account list, activity feed, log viewers.")

t(70, "Implement request deduplication",
  "Update frontend/src/api/client.js to deduplicate concurrent identical requests. "
  "If the same URL+params is already in-flight, return the existing promise instead of making a new request. "
  "Maintain a map of in-flight requests: Map<key, Promise>. "
  "Remove from map when request completes or fails. "
  "Prevents: multiple components mounting and all fetching the same data simultaneously. "
  "Log deduplication events in development mode.")

t(70, "Add API request batching",
  "Create frontend/src/lib/requestBatcher.js — batches multiple API requests into one. "
  "Collect requests made within a 50ms window, combine into a batch request. "
  "Backend: POST /api/batch — accepts array of {method, path, body}, returns array of responses. "
  "Create backend/app/api/batch.py Blueprint that processes batch requests. "
  "Apply to: dashboard loading (fetch all widget data in one request), "
  "multi-store initialization (fetch multiple data types at once). "
  "Max batch size: 20 requests.")

t(70, "Add performance monitoring",
  "Create frontend/src/lib/perfMonitor.js — tracks client-side performance metrics. "
  "Metrics: page load time, route navigation time, API response times (avg, p95, p99), "
  "component render time (for heavy components), WebSocket latency. "
  "Store metrics in memory (last 100 data points per metric). "
  "Add to SystemStatusBar: show avg API response time. "
  "Log slow operations (>2s) to console in development mode. "
  "Optional: report to backend endpoint for monitoring.")

# ═══════════════════════════════════════════════════════
# GROUP 71: Bundle Optimization (6 tasks)
# ═══════════════════════════════════════════════════════
t(71, "Analyze and optimize bundle size",
  "Run: cd frontend && pnpm build && npx vite-bundle-visualizer. "
  "Identify largest chunks and dependencies. "
  "Optimize: tree-shake unused D3 modules (import specific modules, not full d3). "
  "Check for duplicate dependencies. "
  "Check for unnecessarily large packages (can they be replaced with lighter alternatives?). "
  "Target: main bundle < 200KB gzipped, largest lazy chunk < 100KB gzipped. "
  "Document findings and optimizations in docs/bundle-optimization.md.")

t(71, "Configure Vite build optimization",
  "Update frontend/vite.config.js with production optimizations: "
  "build.rollupOptions.output.manualChunks: split vendor code into separate chunks (vue, d3, tiptap, etc.). "
  "build.cssCodeSplit: true (CSS per component). "
  "build.minify: 'terser' with drop_console and drop_debugger. "
  "build.sourcemap: false for production (or 'hidden' for error tracking). "
  "Add compression plugin: vite-plugin-compression for gzip/brotli pre-compression. "
  "Install: cd frontend && pnpm add -D vite-plugin-compression.")

t(71, "Optimize D3 imports",
  "Audit all D3 chart components and replace full d3 imports with specific modules: "
  "Instead of: import * as d3 from 'd3' "
  "Use: import { scaleLinear } from 'd3-scale'; import { axisBottom } from 'd3-axis'; etc. "
  "This enables tree-shaking to remove unused D3 modules. "
  "Common modules needed: d3-scale, d3-axis, d3-shape, d3-selection, d3-transition, d3-format, "
  "d3-time-format, d3-color, d3-interpolate, d3-zoom, d3-drag, d3-force. "
  "Install individual modules if not already available: cd frontend && pnpm add d3-scale d3-axis d3-shape etc.")

t(71, "Add resource preloading hints",
  "Update frontend/index.html and Vite config with resource hints: "
  "<link rel='preload' href='critical-font.woff2' as='font' crossorigin>. "
  "<link rel='preconnect' href='API_BASE_URL'>. "
  "Vite: add preload for critical route chunks. "
  "Add <meta name='viewport' content='width=device-width, initial-scale=1.0'>. "
  "Preload the most common route's chunk (dashboard) on initial page load. "
  "DNS-prefetch for external services (Zep, LLM providers).")

t(71, "Optimize CSS",
  "Audit and optimize CSS: "
  "Remove unused Tailwind classes: add content paths to tailwind.config.js for tree-shaking. "
  "Check for duplicate CSS rules. "
  "Ensure animations.css only includes used animations. "
  "Check that theme CSS variables are defined at :root level only. "
  "Move critical CSS inline for above-the-fold content. "
  "Target: total CSS < 50KB gzipped.")

t(71, "Add build-time optimization checks",
  "Create a build optimization check script: frontend/scripts/check-build.js. "
  "Checks: bundle size within targets, no console.log in production, "
  "all lazy routes properly configured, no full d3 imports, no unused dependencies. "
  "Run as part of: cd frontend && pnpm build (add as postbuild script in package.json). "
  "Warn (don't fail) if checks don't pass. Output report to stdout. "
  "This helps Ralphy agents keep the build optimized as they add features.")

# ═══════════════════════════════════════════════════════
# GROUP 72: Health Monitoring + Error Tracking (6 tasks)
# ═══════════════════════════════════════════════════════
t(72, "Create backend health monitoring service",
  "Create backend/app/services/health_monitor.py — monitors backend health metrics. "
  "HealthMonitor class (singleton): "
  "Track: request count, error count, avg response time, active connections, memory usage. "
  "Expose via: GET /api/health/metrics — returns all metrics as JSON. "
  "Alert thresholds: error rate > 5%, avg response time > 2s, memory > 80%. "
  "Log warnings when thresholds exceeded. "
  "Reset metrics every hour (keep hourly snapshots for last 24 hours). "
  "Thread-safe counters using threading.Lock.")

t(72, "Create frontend error boundary component",
  "Create frontend/src/components/common/ErrorBoundary.vue — catches and handles component errors. "
  "Uses Vue's onErrorCaptured lifecycle hook. "
  "On error: show friendly error message instead of broken UI. "
  "'Something went wrong' card with error details (collapsible), 'Retry' button, 'Report' button. "
  "Log error to console and to backend (POST /api/errors). "
  "Wrap all route components with ErrorBoundary in App.vue. "
  "Different error messages: network error, component error, data error.")

t(72, "Create frontend error tracking service",
  "Create frontend/src/lib/errorTracker.js — tracks and reports frontend errors. "
  "Captures: unhandled JS errors (window.onerror), unhandled promise rejections, "
  "Vue component errors, API request failures. "
  "For each error: stack trace, component tree, route, timestamp, browser info. "
  "Store last 50 errors in memory. "
  "POST /api/errors — send error report to backend for logging. "
  "Backend: POST /api/errors stores in backend/logs/frontend-errors.log. "
  "Configure in main.js: app.config.errorHandler = errorTracker.capture.")

t(72, "Build health dashboard component",
  "Create frontend/src/components/settings/HealthDashboard.vue — displays system health. "
  "Backend health: request rate, error rate, avg response time, memory usage. "
  "Frontend health: recent errors count, performance metrics, cache hit rate. "
  "Service health: LLM, Zep, WebSocket status. "
  "Charts: request rate over time, error rate over time. "
  "Add to SettingsView.vue in a 'System Health' section. "
  "Auto-refresh every 30 seconds.")

t(72, "Create startup diagnostics",
  "Create backend/app/services/diagnostics.py — runs startup diagnostics when the app starts. "
  "Checks: Python version, required packages installed, environment variables set, "
  "data directories exist (data/simulations, data/dashboards, data/templates, data/reports), "
  "LLM provider reachable (if configured), Zep reachable (if configured), "
  "port available, disk space sufficient. "
  "Log results at INFO level. Fail fast on critical issues. "
  "Print a startup summary: 'MiroFish GTM Demo starting in [full/partial/demo] mode.' "
  "Call from run.py before starting the server.")

t(72, "Add structured logging throughout the app",
  "Update backend logging to use structured JSON format: "
  "Each log entry: {timestamp, level, module, message, request_id, extra_data}. "
  "Update all backend services to use Python logging (not print statements). "
  "Log levels: DEBUG for detailed tracing, INFO for operations, WARNING for issues, ERROR for failures. "
  "Configure in backend/app/config.py: log level from environment variable (default INFO). "
  "Log rotation: daily rotation, keep 7 days. "
  "Separate log files: app.log (all), errors.log (errors only), simulation.log (simulation activity).")

# ═══════════════════════════════════════════════════════
# GROUP 73: Railway Deployment Config (4 tasks)
# ═══════════════════════════════════════════════════════
t(73, "Create Railway deployment configuration",
  "Create railway.toml at the project root with build and deploy settings: "
  "[build] builder = 'DOCKERFILE'. "
  "Create Procfile for each service if needed. "
  "Verify Dockerfiles (backend/Dockerfile and frontend/Dockerfile) work for Railway: "
  "backend should expose PORT env var, frontend should serve built files. "
  "Add .railwayignore: node_modules, __pycache__, .git, .env, backend/logs, log. "
  "Document Railway environment variables needed in docs/deployment.md.")

t(73, "Configure environment-aware settings",
  "Update backend/app/config.py to support Railway-specific settings: "
  "RAILWAY_ENVIRONMENT: detect if running on Railway. "
  "PORT: use Railway's provided PORT env var. "
  "DATABASE_URL: ready for if/when database is added. "
  "FRONTEND_URL: for CORS configuration. "
  "Update frontend/vite.config.js: VITE_API_BASE_URL env var for production API URL. "
  "Ensure all env vars have sensible defaults for local development.")

t(73, "Create docker-compose production profile",
  "Update docker-compose.yml to add a 'production' profile: "
  "docker compose --profile production up. "
  "Production differences: no volume mounts, no debug mode, environment variables from .env.production. "
  "Add docker-compose.prod.yml for production-specific overrides. "
  "Backend: gunicorn with 4 workers. Frontend: nginx serving built files. "
  "Add healthcheck to both services. "
  "Verify: docker compose --profile production up -d && curl localhost:3000")

t(73, "Create deployment documentation",
  "Create docs/deployment.md with deployment instructions: "
  "Section 1: Local Development — docker compose up, individual service startup. "
  "Section 2: Docker Production — docker compose --profile production up. "
  "Section 3: Railway Deployment — how to deploy, required env vars, service configuration. "
  "Section 4: Environment Variables — complete reference table with descriptions and defaults. "
  "Section 5: Troubleshooting — common issues and solutions. "
  "Keep documentation concise and actionable.")

# ═══════════════════════════════════════════════════════
# GROUP 74: OAuth Flow (8 tasks)
# ═══════════════════════════════════════════════════════
t(74, "Create OAuth configuration",
  "Create backend/auth/oauth_config.py — OAuth provider configuration. "
  "Support Google OAuth (for @intercom.io login) and generic OIDC. "
  "Config: OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI, OAUTH_PROVIDER (google|okta). "
  "ALLOWED_EMAIL_DOMAINS: comma-separated list (default: 'intercom.io'). "
  "All OAuth settings optional — when not configured, auth is disabled. "
  "Use python-jose for JWT handling, requests-oauthlib for OAuth flow (add to requirements.txt). "
  "Or use a lightweight alternative if those are too heavy.")

t(74, "Create OAuth flow endpoints",
  "Create backend/auth/oauth_routes.py as a Flask Blueprint: "
  "GET /auth/login — redirects to Google/Okta OAuth consent page. "
  "GET /auth/callback — handles OAuth callback, validates token, creates session. "
  "POST /auth/logout — destroys session, redirects to landing. "
  "GET /auth/me — returns current user info (or 401 if not authenticated). "
  "Validate: email must be in ALLOWED_EMAIL_DOMAINS. Reject others with friendly error. "
  "Create JWT session token, set as httpOnly cookie. "
  "Register Blueprint with url_prefix='/auth'.")

t(74, "Create auth middleware",
  "Create backend/auth/middleware.py — authentication middleware. "
  "auth_required decorator: checks for valid JWT cookie, returns 401 if missing/expired. "
  "auth_optional decorator: attaches user info to g if authenticated, continues if not. "
  "Check JWT validity: signature, expiration, email domain. "
  "When AUTH_ENABLED=false: all requests pass through (no auth required). "
  "When AUTH_ENABLED=true: protected routes require auth, public routes (/api/health, /auth/*) exempt. "
  "Add user info to g.user for use in request handlers.")

t(74, "Build login page Vue component",
  "Create frontend/src/views/LoginView.vue (update if exists) — OAuth login page. "
  "Intercom-branded login: logo, 'Sign in to MiroFish GTM Demo' heading. "
  "'Continue with Google' button (styled per Google's branding guidelines). "
  "'Continue with Okta' button (if Okta configured). "
  "Loading state while OAuth redirect happens. "
  "Error state: 'Access denied — @intercom.io email required' with retry option. "
  "If AUTH_ENABLED=false: show a 'Skip Authentication (Demo Mode)' link.")

t(74, "Create auth composable and store",
  "Create frontend/src/composables/useAuth.js — authentication composable. "
  "Reactive state: user (object|null), isAuthenticated (boolean), isLoading (boolean). "
  "Methods: login(), logout(), checkAuth(). "
  "On app mount: call GET /auth/me to check existing session. "
  "If 401: user is null, redirect to login if auth required. "
  "Provide/inject for app-wide access. "
  "Also update frontend/src/stores/auth.js Pinia store with user info.")

t(74, "Add auth guards to router",
  "Update frontend/src/router/index.js to add navigation guards: "
  "beforeEach: check if route requires auth (meta.requiresAuth). "
  "If requires auth and not authenticated: redirect to /login with return URL. "
  "If authenticated: proceed. "
  "Public routes (no auth required): /login, / (landing). "
  "All other routes: require auth when AUTH_ENABLED=true. "
  "When AUTH_ENABLED=false: all routes accessible without auth.")

t(74, "Build user menu component",
  "Create frontend/src/components/common/UserMenu.vue — user dropdown in the navbar. "
  "Shows: user avatar (from Google profile), user name, email. "
  "Dropdown: 'Settings', 'Keyboard Shortcuts', divider, 'Sign Out'. "
  "When not authenticated: show 'Sign In' button instead. "
  "Avatar: circular image from Google profile, or initials fallback. "
  "Add to AppNav.vue in the top-right corner.")

t(74, "Create session management",
  "Create backend/auth/session_manager.py — manages user sessions. "
  "JWT tokens with 24-hour expiration. Refresh on activity. "
  "Session data stored in JWT (stateless): user_id, email, name, picture_url, role, issued_at. "
  "Token refresh: if token expires in <1 hour, issue new token on next request. "
  "Rate limiting per user: max 100 API requests per minute. "
  "Session logging: log login, logout, refresh events.")

# ═══════════════════════════════════════════════════════
# GROUP 75: Role-Based Access (8 tasks)
# ═══════════════════════════════════════════════════════
t(75, "Create role-based access control model",
  "Create backend/auth/rbac.py — role-based access control system. "
  "Roles: admin (full access), editor (create/edit simulations, reports), viewer (read-only), guest (limited views). "
  "Permissions: view_simulations, create_simulations, edit_simulations, delete_simulations, "
  "view_reports, create_reports, manage_agents, manage_templates, manage_settings, manage_users. "
  "Role-permission mapping: admin=all, editor=all except manage_users/manage_settings, "
  "viewer=view_* only, guest=view_simulations + view_reports only. "
  "Store user roles in backend/data/users.json (simple file-based for now).")

t(75, "Create permission checking middleware",
  "Create backend/auth/permissions.py — permission checking decorators. "
  "requires_permission(permission): decorator that checks g.user has required permission. "
  "Returns 403 with descriptive error if denied. "
  "requires_role(role): checks user has specified role or higher (admin > editor > viewer > guest). "
  "Apply to API routes: POST/PUT/DELETE routes require editor+, admin routes require admin. "
  "GET routes: generally viewer+, but some admin-only (settings, user management).")

t(75, "Create user management API",
  "Add to backend/auth/oauth_routes.py or create backend/auth/user_management.py Blueprint: "
  "GET /auth/users — list all users with roles (admin only). "
  "PUT /auth/users/<email>/role — change user role (admin only). "
  "DELETE /auth/users/<email> — remove user access (admin only). "
  "GET /auth/roles — list available roles with permissions. "
  "POST /auth/users/invite — invite user by email (admin only, sends email or generates link). "
  "First user to log in automatically gets admin role.")

t(75, "Build role-based UI visibility",
  "Create frontend/src/composables/usePermissions.js — checks user permissions for UI rendering. "
  "can(permission): returns boolean. "
  "hasRole(role): returns boolean. "
  "Use with v-if: <button v-if='can(\"create_simulations\")'>New Simulation</button>. "
  "Hide UI elements user can't access (buttons, menu items, entire sections). "
  "Show read-only indicators for viewers: disable edit controls, hide delete buttons. "
  "Guest mode: show limited navigation, hide admin features.")

t(75, "Build user management component",
  "Create frontend/src/components/settings/UserManagement.vue — admin panel for managing users. "
  "Table: email, name, role (dropdown selector), last active, actions (remove). "
  "Only visible to admins. 'Invite User' button with email input. "
  "Role change confirmation dialog: 'Change [name] from [old role] to [new role]?' "
  "Remove user confirmation: 'Remove [name]'s access? They can re-login but will get guest role.' "
  "Add to SettingsView.vue in an 'User Management' section (admin only).")

t(75, "Add role indicators to UI",
  "Show role-related indicators throughout the UI: "
  "UserMenu: show role badge (Admin, Editor, Viewer, Guest). "
  "Locked features: show lock icon with 'Requires Editor role' tooltip on viewer-restricted actions. "
  "Admin banner: subtle 'Admin' badge in navbar for admins. "
  "Guest banner: 'Guest access — some features are limited' info bar. "
  "Permission denied page: friendly message when accessing restricted URL directly.")

t(75, "Add audit logging for role changes",
  "Create backend/auth/audit_log.py — logs security-relevant events. "
  "Log: login, logout, role_change, user_removed, permission_denied. "
  "Each entry: timestamp, actor_email, action, target, details. "
  "Store in backend/logs/audit.log (JSON format, one entry per line). "
  "API: GET /auth/audit-log?limit=50 — admin only. "
  "Retention: keep 90 days of audit logs.")

t(75, "Create permission-aware API responses",
  "Update all API endpoints to respect user permissions: "
  "Simulation endpoints: viewers can GET, editors can POST/PUT, only creator or admin can DELETE. "
  "Dashboard endpoints: viewers see shared dashboards, editors create/edit own, admin sees all. "
  "Settings endpoints: viewers see settings, editors change own, admin changes all. "
  "Report endpoints: viewers read, editors generate/save, admin manages templates. "
  "Add 'permissions' field to API responses: list of actions the current user can take on this resource.")

# ═══════════════════════════════════════════════════════
# GROUP 76: CHECKPOINT (1 task)
# ═══════════════════════════════════════════════════════
t(76, "CHECKPOINT: Verify app builds and runs after security and auth features",
  "Run comprehensive build and smoke test: "
  "1) cd frontend && pnpm install && pnpm build — verify no build errors. "
  "2) cd backend && pip install -r requirements.txt — verify auth dependencies install. "
  "3) Verify auth works in disabled mode: AUTH_ENABLED=false, all routes accessible. "
  "4) Verify RBAC imports: python -c 'from auth.rbac import Role, Permission'. "
  "5) Verify OAuth routes registered. "
  "6) Test demo mode still works end-to-end without any auth configuration. "
  "7) Check no security regressions: no exposed API keys, no hardcoded secrets. "
  "8) Verify ServiceWorker registration works. "
  "9) Verify WebSocket connections work. "
  "10) Full route count check: list all registered routes on backend and frontend. "
  "Fix issues. Create docs/checkpoint-group-76.md.")

# ═══════════════════════════════════════════════════════
# GROUP 77: API Key Management + Audit + CSRF (8 tasks)
# ═══════════════════════════════════════════════════════
t(77, "Create API key management system",
  "Create backend/auth/api_keys.py — manages programmatic API access keys. "
  "ApiKeyManager class: "
  "generate_key(user_email, name, permissions) → api_key string. "
  "validate_key(api_key) → user info and permissions. "
  "revoke_key(key_id). list_keys(user_email). "
  "Keys: prefix 'mf_' + 32 random characters. Store hashed (SHA-256) in backend/data/api_keys.json. "
  "Each key has: id, name, prefix (first 8 chars for identification), created_at, last_used, permissions. "
  "Keys can be scoped: read_only, full_access, simulation_only.")

t(77, "Add API key authentication to middleware",
  "Update backend/auth/middleware.py to support API key authentication: "
  "Check Authorization header: 'Bearer mf_...' format. "
  "If API key: validate and set g.user from key's associated user. "
  "If JWT cookie: use existing OAuth session auth. "
  "API key auth takes precedence over session auth (for programmatic access). "
  "Rate limiting per API key: configurable per key (default 60/min).")

t(77, "Build API key management component",
  "Create frontend/src/components/settings/ApiKeyManagement.vue — manage API keys. "
  "Create new key: name input, permission scope selector, 'Generate' button. "
  "Show key ONCE on creation (modal with copy button and warning: 'This won't be shown again'). "
  "List existing keys: name, prefix, created date, last used, permissions, 'Revoke' button. "
  "Revoke confirmation dialog. "
  "Add to SettingsView.vue in an 'API Keys' section.")

t(77, "Add CSRF protection",
  "Create backend/auth/csrf.py — CSRF protection middleware. "
  "Generate CSRF token: random string set as cookie + included in HTML response. "
  "Validate: POST/PUT/DELETE requests must include CSRF token in X-CSRF-Token header. "
  "Exempt: API key authenticated requests (they don't need CSRF). "
  "Exempt: /auth/callback (OAuth callback). "
  "Frontend: read CSRF token from cookie, include in API client request headers. "
  "Update frontend/src/api/client.js to include CSRF token in all mutating requests.")

t(77, "Create comprehensive audit log",
  "Extend backend/auth/audit_log.py to log all important operations: "
  "Auth events: login, logout, key_created, key_revoked. "
  "Data events: simulation_created, simulation_deleted, report_generated, dashboard_saved. "
  "Admin events: role_changed, user_removed, settings_updated. "
  "Each entry: timestamp, user, action, resource_type, resource_id, details, ip_address. "
  "API: GET /auth/audit?action=login&user=email&since=date — filterable audit log. "
  "Frontend: AuditLogViewer component in settings (admin only).")

t(77, "Build audit log viewer component",
  "Create frontend/src/components/settings/AuditLogViewer.vue — displays audit trail. "
  "Table: timestamp, user, action, resource, details. "
  "Filters: action type, user, date range. Search by resource or detail text. "
  "Timeline view: chronological with daily grouping. "
  "Export as CSV. Admin only access. "
  "Add to SettingsView.vue in a 'Security & Audit' section.")

t(77, "Add rate limiting to all API endpoints",
  "Create backend/app/middleware/rate_limiter.py — per-endpoint rate limiting. "
  "Use a simple in-memory token bucket algorithm. "
  "Default limits: 60 requests/min for GET, 30/min for POST, 10/min for DELETE. "
  "Simulation start: 5/min (prevent simulation spam). "
  "Report generation: 10/min. "
  "Return 429 Too Many Requests with Retry-After header when limit exceeded. "
  "Per-user limits (by email or API key). "
  "Add to response headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset.")

t(77, "Add security headers middleware",
  "Create backend/app/middleware/security_headers.py — adds security headers to all responses. "
  "Headers: Content-Security-Policy (restrict script/style sources), "
  "X-Content-Type-Options: nosniff, X-Frame-Options: DENY, "
  "X-XSS-Protection: 1; mode=block, Strict-Transport-Security (for production), "
  "Referrer-Policy: strict-origin-when-cross-origin. "
  "Register in app factory. Don't break development (CSP needs to allow localhost).")

# ═══════════════════════════════════════════════════════
# GROUPS 78-83: Testing (32 tasks compressed)
# ═══════════════════════════════════════════════════════
t(78, "Set up E2E testing with Playwright",
  "Install Playwright for Vue: cd frontend && pnpm add -D @playwright/test. "
  "Create frontend/e2e/playwright.config.ts with: baseURL localhost:3000, headless mode, "
  "screenshot on failure, video on failure. "
  "Create frontend/e2e/fixtures/test-data.ts with test data helpers. "
  "Verify setup: create a simple test that navigates to / and checks the title.")

t(78, "E2E test: landing page and navigation",
  "Create frontend/e2e/landing.spec.ts: "
  "Test: landing page loads with Intercom branding. "
  "Test: all navigation links work (click each nav item, verify route change). "
  "Test: page transitions are smooth (no blank flashes). "
  "Test: dark mode toggle works. "
  "Test: keyboard shortcut '?' opens help modal.")

t(78, "E2E test: scenario creation and simulation launch",
  "Create frontend/e2e/simulation.spec.ts: "
  "Test: navigate to scenario builder, select a template, launch simulation. "
  "Test: simulation controls appear (play, pause, stop). "
  "Test: messages appear in the live feed (demo mode). "
  "Test: simulation completes and shows results. "
  "Test: replay controls work (play, step forward/back).")

t(78, "E2E test: GTM dashboard data display",
  "Create frontend/e2e/gtm-dashboard.spec.ts: "
  "Test: dashboard loads with KPI cards showing data. "
  "Test: charts render (check for SVG elements). "
  "Test: activity feed shows items. "
  "Test: top accounts table has rows and is sortable. "
  "Test: navigation to sub-pages works (revenue, pipeline, etc.).")

t(79, "E2E test: report generation flow",
  "Create frontend/e2e/report.spec.ts: "
  "Test: navigate to reports, click 'Generate'. "
  "Test: report wizard steps work (select simulation, choose type, configure, generate). "
  "Test: generated report renders with sections and charts. "
  "Test: export button works (copy to clipboard). "
  "Test: report builder opens and sections can be added.")

t(79, "E2E test: settings and service configuration",
  "Create frontend/e2e/settings.spec.ts: "
  "Test: settings page loads with all sections. "
  "Test: theme switcher changes theme colors. "
  "Test: service status shows connectivity info. "
  "Test: demo mode banner appears when no API keys configured.")

t(79, "E2E test: agent management",
  "Create frontend/e2e/agents.spec.ts: "
  "Test: agents page loads with template agents. "
  "Test: agent creation wizard: fill basic info, configure personality, save. "
  "Test: created agent appears in the list. "
  "Test: agent persona card shows correct information.")

t(79, "E2E test: data views load correctly",
  "Create frontend/e2e/data-views.spec.ts: "
  "Test: Salesforce view loads with accounts and pipeline. "
  "Test: CPQ view loads with products and quotes. "
  "Test: Revenue view loads with MRR waterfall and trends. "
  "Test: Pipeline view loads with funnel and conversion charts. "
  "Test: Orders view loads with timeline and provisioning dashboard.")

t(80, "API integration tests: simulation endpoints",
  "Create backend/tests/test_simulation_api.py using pytest. "
  "Test: POST /api/simulation/start — creates simulation, returns ID. "
  "Test: GET /api/simulation/<id>/status — returns status. "
  "Test: GET /api/simulation/<id>/metrics — returns metrics. "
  "Test: Demo mode produces consistent mock data. "
  "Test: Invalid simulation ID returns 404. "
  "Use Flask test client. Run with: cd backend && python -m pytest tests/.")

t(80, "API integration tests: GTM data endpoints",
  "Create backend/tests/test_gtm_data_api.py: "
  "Test: GET /api/salesforce/accounts — returns paginated accounts. "
  "Test: GET /api/cpq/quotes — returns quotes with status filter. "
  "Test: GET /api/pipeline/funnel — returns funnel data. "
  "Test: GET /api/revenue/metrics — returns monthly metrics. "
  "Test: GET /api/orders — returns orders. "
  "Test: All endpoints work without API keys (demo mode).")

t(80, "API integration tests: report and template endpoints",
  "Create backend/tests/test_report_template_api.py: "
  "Test: GET /api/templates — returns scenario templates. "
  "Test: GET /api/templates/<id> — returns single template. "
  "Test: POST /api/reports/generate — starts report generation. "
  "Test: GET /api/dashboards — returns dashboards. "
  "Test: POST /api/dashboards — creates dashboard.")

t(80, "API integration tests: auth endpoints",
  "Create backend/tests/test_auth_api.py: "
  "Test: GET /auth/me — returns 401 when not authenticated. "
  "Test: With AUTH_ENABLED=false, all endpoints accessible. "
  "Test: API key validation works. "
  "Test: CSRF token generation and validation. "
  "Test: Rate limiting returns 429.")

t(81, "Component unit tests: chart components",
  "Create frontend/src/components/charts/__tests__/ with tests for chart components: "
  "Test RadarChart: renders SVG, correct number of axes, handles empty data. "
  "Test BarChartWidget: renders bars, shows labels, handles zero values. "
  "Test DonutChartWidget: renders arcs, shows center text, handles single segment. "
  "Use Vitest + @vue/test-utils. Mount components with sample data, check DOM output.")

t(81, "Component unit tests: simulation components",
  "Create frontend/src/components/simulation/__tests__/ with tests: "
  "Test PersonaCard: renders agent name, role, personality radar. "
  "Test SimulationControls: start/pause/stop buttons, progress bar. "
  "Test LiveFeed: renders messages, auto-scrolls, shows agent names. "
  "Test DebateView: renders For/Against columns. "
  "Use mock data, verify DOM rendering.")

t(81, "Unit tests: Pinia stores",
  "Create frontend/src/stores/__tests__/ with store tests: "
  "Test salesforce store: fetchAccounts populates state, getters compute correctly. "
  "Test simulation store: state transitions (created→running→completed). "
  "Test settings store: theme changes persist, defaults are correct. "
  "Use Pinia test utilities. Mock API calls. "
  "Verify loading/error states are managed correctly.")

t(81, "Unit tests: backend services",
  "Create backend/tests/test_services.py with unit tests for key services: "
  "Test sfdc_data_generator: generates correct number of accounts, realistic values. "
  "Test revenue_data_generator: MRR progression makes sense, no negative values where inappropriate. "
  "Test reconciliation_generator: correct percentage of discrepancies. "
  "Test scenario_templates: all template files parse as valid JSON. "
  "Run with: cd backend && python -m pytest tests/test_services.py.")

t(82, "Accessibility audit and fixes",
  "Run accessibility audit on key pages: "
  "1) Check color contrast ratios (WCAG AA minimum). "
  "2) Verify all images/icons have alt text or aria-label. "
  "3) Verify keyboard navigation: Tab through all interactive elements. "
  "4) Verify screen reader compatibility: proper heading hierarchy, ARIA roles on custom widgets. "
  "5) Verify focus management: modals trap focus, focus returns on close. "
  "6) Check prefers-reduced-motion is respected. "
  "Fix top 10 accessibility issues found. "
  "Create docs/accessibility-audit.md with findings and fixes.")

t(82, "Visual regression baseline screenshots",
  "Create frontend/e2e/visual-regression.spec.ts — captures baseline screenshots. "
  "Pages: landing, dashboard, simulation workspace, report viewer, settings. "
  "Light and dark mode for each page. "
  "Use Playwright's screenshot comparison with 1% threshold. "
  "Save baseline screenshots in frontend/e2e/screenshots/baseline/. "
  "Document how to update baselines when intentional visual changes are made.")

t(83, "Performance benchmark: page load times",
  "Create frontend/e2e/performance.spec.ts — measures critical page load times. "
  "Measure: landing page LCP, dashboard TTFB, simulation workspace TTI. "
  "Targets: LCP < 2s, TTFB < 200ms, TTI < 3s. "
  "Run 5 times, take median. Report in a simple table format. "
  "If using Playwright, use page.evaluate with Performance API. "
  "Create docs/performance-benchmarks.md with results.")

t(83, "Performance benchmark: API response times",
  "Create backend/tests/test_performance.py — measures API response times. "
  "Measure: /api/health (baseline), /api/salesforce/accounts, /api/revenue/metrics, "
  "/api/simulation endpoints, /api/templates. "
  "Targets: health < 10ms, data endpoints < 100ms, simulation start < 500ms. "
  "Run each 10 times, report p50, p95, p99. "
  "Flag any endpoints exceeding targets. "
  "Append results to docs/performance-benchmarks.md.")

# ═══════════════════════════════════════════════════════
# GROUPS 84-89: Documentation & Demo (21 tasks compressed)
# ═══════════════════════════════════════════════════════
t(84, "Create interactive tutorial system",
  "Create frontend/src/components/tutorial/TutorialSystem.vue — step-by-step tutorial overlay. "
  "TutorialStep: { target: CSS selector, title, description, position: top|right|bottom|left }. "
  "Highlight target element with spotlight (dim everything else). "
  "Show tooltip next to target with step content. Next/Previous/Skip buttons. "
  "Create 'Welcome Tour' tutorial: 5 steps covering nav, dashboard, simulations, reports, settings. "
  "Trigger on first visit (check localStorage). Also accessible from Help menu. "
  "Use CSS pointer-events to prevent interaction with non-target elements during tutorial.")

t(84, "Create guided scenario walkthrough",
  "Create frontend/src/components/tutorial/ScenarioWalkthrough.vue — guided demo walkthrough. "
  "Pre-scripted walkthrough: 1) Select 'Pipeline Review' template, 2) Configure agents, "
  "3) Start simulation, 4) Watch messages flow, 5) Review results, 6) Generate report. "
  "Each step has a narration text box and 'Do This' action button that performs the action. "
  "Auto-advance option: walkthrough proceeds automatically (for passive demo viewing). "
  "Manual mode: user follows instructions at their own pace. "
  "Timer: show estimated remaining time for the walkthrough.")

t(84, "Build contextual help system",
  "Create frontend/src/components/common/ContextualHelp.vue — inline help for features. "
  "Small '?' icon next to complex features. Click to show a tooltip with explanation. "
  "Help content database: frontend/src/data/help-content.js — map of feature → explanation. "
  "Features to document: OASIS simulation, Zep knowledge graph, personality dynamics, "
  "coalition detection, what-if analysis, scenario branching, D3 visualizations. "
  "Each help entry: title, short description, 'Learn More' link to full docs.")

t(84, "Create keyboard shortcut quick reference card",
  "Create frontend/src/components/common/ShortcutQuickRef.vue — floating quick reference card. "
  "Shows top 10 most useful shortcuts in a compact card format. "
  "Triggered by Ctrl/Cmd+/ or from Help menu. "
  "Pinnable: stays visible while using the app. Draggable to reposition. "
  "Context-aware: shows relevant shortcuts for current page. "
  "Link to full shortcuts modal for complete list.")

t(85, "Create architecture documentation",
  "Create docs/architecture.md — comprehensive system architecture doc. "
  "Sections: System Overview (ASCII diagram), Backend Architecture (Flask + Blueprints + Services), "
  "Frontend Architecture (Vue 3 + Pinia + Router), "
  "Data Flow (how data moves from generators → API → stores → components), "
  "Real-time Architecture (WebSocket events), "
  "OASIS Integration (how simulation engine works), "
  "Zep Integration (how knowledge graph is built), "
  "Authentication Flow (OAuth → JWT → RBAC). "
  "Keep it concise — architecture overview, not code documentation.")

t(85, "Create ADR (Architecture Decision Records)",
  "Create docs/adr/ directory with Architecture Decision Records: "
  "001-vue3-composition-api.md — why Vue 3 with Composition API over Options API. "
  "002-flask-blueprints.md — why Flask Blueprints over monolithic app. "
  "003-d3-for-visualizations.md — why D3.js over Chart.js or other libraries. "
  "004-pinia-state-management.md — why Pinia over Vuex. "
  "005-oasis-camel-ai.md — why OASIS/camel-ai for multi-agent simulation. "
  "006-zep-for-memory.md — why Zep Cloud for knowledge graph and agent memory. "
  "Each ADR: Status, Context, Decision, Consequences. Keep each under 1 page.")

t(85, "Create API documentation page",
  "Create docs/api-reference.md — comprehensive API endpoint reference. "
  "Group by Blueprint: Health, Salesforce, CPQ, Pipeline, Revenue, Orders, Reconciliation, "
  "Simulation, Reports, Templates, Dashboards, Campaigns, Analytics, Auth. "
  "Each endpoint: method, path, description, parameters, example response. "
  "Keep it auto-generatable: use Flask's url_map to list all routes. "
  "Create a script: backend/scripts/generate_api_docs.py that outputs Markdown from route inspection.")

t(86, "CHECKPOINT: Verify app builds and documentation is complete",
  "Run final comprehensive build and smoke test: "
  "1) cd frontend && pnpm install && pnpm build — clean build, no warnings. "
  "2) cd frontend && pnpm lint — no errors. "
  "3) cd backend && pip install -r requirements.txt — all deps install. "
  "4) cd frontend && pnpm test — all unit tests pass. "
  "5) cd backend && python -m pytest — all backend tests pass. "
  "6) Verify docs exist: architecture.md, api-reference.md, deployment.md, ADRs. "
  "7) Verify all checkpoint docs exist (groups 25, 36, 46, 56, 66, 76). "
  "8) Count total: components, routes, API endpoints, tests. "
  "Fix any issues. Create docs/checkpoint-group-86.md with comprehensive project statistics.")

t(87, "Create Marp presentation slides",
  "Create docs/slides.md — Marp-formatted presentation for the demo. "
  "Slides: 1) Title: 'MiroFish GTM Demo — Swarm Intelligence for GTM Operations' "
  "2) Problem: GTM teams make decisions in silos with incomplete information "
  "3) Solution: Multi-agent simulation using real AI (OASIS + Zep) "
  "4) Architecture overview (simplified diagram) "
  "5) Live Demo walkthrough plan (what to show) "
  "6) Key features: real LLM agents, knowledge graph, personality dynamics, coalition detection "
  "7) GTM-specific scenarios: pipeline review, competitive response, MRR reconciliation "
  "8) Visualizations showcase: D3 charts, network graphs, animated flows "
  "9) Technical highlights: Vue 3, Flask, WebSocket, demo mode fallback "
  "10) Q&A "
  "Use Intercom brand colors. Keep text minimal, focus on visuals.")

t(87, "Create demo script document",
  "Create docs/demo-script.md — step-by-step script for live demo presentation. "
  "Duration: 10-15 minutes. "
  "Steps: 1) Show landing page with Intercom branding (30s) "
  "2) Navigate GTM Dashboard, highlight KPIs and visualizations (2min) "
  "3) Show Salesforce, Revenue, Pipeline data views (2min) "
  "4) Open scenario builder, select 'Pipeline Review' template (1min) "
  "5) Launch simulation, watch agents discuss in real-time (3min) "
  "6) Show agent reasoning transparency — thinking process (1min) "
  "7) Show knowledge graph building in real-time (1min) "
  "8) Show coalition formation and sentiment analysis (1min) "
  "9) Generate AI-powered report from simulation results (1min) "
  "10) Show dashboard builder — drag widgets (1min) "
  "Talking points for each step. Backup plan if something fails (demo mode).")

t(87, "Create demo data preset",
  "Create backend/data/demo-preset/ — curated demo data for presentations. "
  "Pre-generate: a completed simulation with interesting outcomes (coalitions, belief changes, key decisions). "
  "Pre-generate: a report from that simulation. "
  "Pre-generate: a custom dashboard with the most impressive widgets. "
  "Load this preset when DEMO_PRESET=true in environment. "
  "The demo preset should tell a compelling story: agents debated pipeline strategy, "
  "formed coalitions around growth vs conservation, eventually reached consensus. "
  "Save as JSON fixtures that can be loaded by the data generators.")

t(88, "Create comprehensive README update",
  "Update README.md at project root with comprehensive project information: "
  "Project description with value proposition. "
  "Quick Start (3 commands to run). "
  "Feature list with brief descriptions. "
  "Architecture overview (high-level). "
  "Development setup instructions. "
  "Testing instructions. "
  "Deployment options. "
  "Contributing guidelines. "
  "License. "
  "Keep it clean and scannable — use badges, headers, and brief descriptions.")

t(88, "Create CHANGELOG",
  "Create CHANGELOG.md tracking all major features added during this build sprint. "
  "Group by feature area: GTM Data (groups 17-24), OASIS Integration (26-33), "
  "Visualizations (34-41), Agent Intelligence (42-49), Scenarios (50-55), "
  "Reporting (56-61), UX Polish (62-67), Infrastructure (68-73), Security (74-77), "
  "Testing (78-83), Documentation (84-89). "
  "For each area: list 3-5 key features with one-line descriptions. "
  "Use Keep a Changelog format (Added, Changed, Improved sections).")

t(89, "Final smoke test across all features",
  "Comprehensive manual smoke test script: "
  "1) Start app: docker compose up OR backend + frontend separately. "
  "2) Landing page loads with branding. "
  "3) Navigate every page: dashboard, salesforce, cpq, pipeline, revenue, orders, "
  "reconciliation, data pipeline, campaigns, analytics, simulations, agents, reports, settings. "
  "4) Start a simulation (demo mode). Verify messages flow. "
  "5) Generate a report. Verify it renders. "
  "6) Check dark mode on 3 pages. "
  "7) Check keyboard shortcuts work. "
  "8) Check command palette (Cmd+K). "
  "9) Verify no console errors on any page. "
  "10) Verify all charts render (no blank SVGs). "
  "Document results in docs/smoke-test-results.md. Fix any critical issues.")

t(89, "Brand consistency pass",
  "Audit all pages for Intercom brand consistency: "
  "1) Primary blue #2068FF used consistently for buttons and accents. "
  "2) Navy #050505 used for headings and dark elements. "
  "3) Orange #ff5600 used only for Fin-related elements and CTAs. "
  "4) Typography consistent: system-ui font, proper heading hierarchy. "
  "5) Spacing consistent: 8px grid (multiples of 8 for padding/margins). "
  "6) Card styles consistent: same border radius, shadow, padding across all cards. "
  "7) Badge styles consistent: same border radius and sizing. "
  "8) Icon usage consistent: same icon library and sizes throughout. "
  "Fix top 10 inconsistencies found. "
  "Create docs/brand-audit.md with findings.")

# ═══════════════════════════════════════════════════════
# GROUPS 90-95: Heavyweight/Stretch Features (30 tasks)
# ═══════════════════════════════════════════════════════
t(90, "Set up i18n framework",
  "Install Vue i18n: cd frontend && pnpm add vue-i18n. "
  "Create frontend/src/i18n/index.js — i18n configuration. "
  "Create frontend/src/i18n/en.json — English translations. "
  "Structure: nested by page/component: {dashboard: {title: 'GTM Dashboard', ...}, simulation: {...}}. "
  "Register i18n plugin in main.js. "
  "Create useI18n composable wrapper for consistent usage.")

t(90, "Extract UI strings for i18n",
  "Audit all Vue components and replace hardcoded strings with i18n keys: "
  "Navigation items: $t('nav.dashboard'), $t('nav.simulations'), etc. "
  "Page titles: $t('dashboard.title'), $t('simulation.title'), etc. "
  "Button labels: $t('common.save'), $t('common.cancel'), $t('common.delete'). "
  "Status messages: $t('status.loading'), $t('status.error'). "
  "Focus on high-visibility strings first (navigation, page titles, buttons). "
  "Don't need to extract every single string — focus on user-facing text.")

t(90, "Add language switcher",
  "Create frontend/src/components/settings/LanguageSwitcher.vue — language selection UI. "
  "Dropdown: English (default), with placeholder entries for future languages. "
  "Add to settings page. "
  "Persist selection to localStorage. "
  "Hot-switch: change language without page reload. "
  "Show language flag icons next to names.")

t(90, "Create Japanese translation file",
  "Create frontend/src/i18n/ja.json — Japanese translations for key UI elements. "
  "Translate: navigation items, page titles, common buttons, status messages. "
  "Use proper Japanese business terminology for GTM concepts. "
  "Don't need to translate every string — focus on the most visible 100 strings. "
  "This is a stretch feature — basic coverage is sufficient.")

t(90, "Add i18n to date and number formatting",
  "Update all date and number formatting to use i18n-aware formatters: "
  "Dates: use Intl.DateTimeFormat with locale parameter. "
  "Numbers: use Intl.NumberFormat with locale parameter. "
  "Currency: use Intl.NumberFormat with currency style and locale. "
  "Update chartUtils.js formatCurrency and formatNumber to accept locale. "
  "This ensures numbers and dates display correctly for all locales.")

t(90, "Add RTL support preparation",
  "Add CSS logical properties where possible: "
  "margin-left → margin-inline-start. padding-right → padding-inline-end. "
  "text-align: left → text-align: start. "
  "Add dir='ltr' to html element (changeable via i18n config). "
  "This is preparation only — don't need to fully support RTL, just avoid blocking it.")

t(91, "Audit and fix mobile layout issues",
  "Test all pages at 375px width (iPhone SE). Fix critical layout issues: "
  "Navigation: collapse to hamburger menu on mobile. "
  "Dashboard: stack all cards vertically. "
  "Charts: ensure they resize to container (responsive SVG). "
  "Tables: horizontal scroll for wide tables. "
  "Modals: full-screen on mobile. "
  "Fix top 20 most visible layout issues.")

t(91, "Create mobile navigation component",
  "Create frontend/src/components/layout/MobileNav.vue — mobile-friendly navigation. "
  "Hamburger menu icon that opens a full-screen overlay navigation. "
  "Large touch-friendly links. Category grouping. Close button. "
  "Swipe gesture to open/close (optional). "
  "Show on screens < 768px width. Hide desktop nav on mobile. "
  "Use media query: @media (max-width: 768px).")

t(91, "Optimize touch interactions",
  "Update interactive components for touch: "
  "Charts: larger touch targets for tooltips and interactive elements. "
  "Buttons: minimum 44px × 44px touch target. "
  "Drag-and-drop: use touch events (touchstart, touchmove, touchend). "
  "Swipe: add swipe gesture support for navigation between views. "
  "Remove hover-dependent interactions on mobile (use click instead). "
  "Test with Chrome DevTools device emulation.")

t(91, "Create mobile-optimized dashboard",
  "Create a mobile-specific dashboard layout: "
  "Stack KPI cards in a 2×2 grid. "
  "Charts: one per row, horizontally scrollable collection. "
  "Activity feed: card-based instead of table-based. "
  "Use smaller font sizes for dense data. "
  "Add pull-to-refresh gesture. "
  "Prioritize content: show most important metrics first on mobile.")

t(91, "Optimize mobile chart rendering",
  "Update D3 chart components for mobile: "
  "Reduce data density: show fewer data points on small screens. "
  "Larger axis labels and tick marks. "
  "Tooltips: position to avoid screen edges. "
  "Remove non-essential chart elements on mobile (legends inline, hide grid lines). "
  "Use simple gestures: pinch-zoom for large charts, swipe for timeline. "
  "Test each chart type at 375px width.")

t(92, "Create PWA manifest",
  "Create frontend/public/manifest.json: "
  "{ name: 'MiroFish GTM Demo', short_name: 'MiroFish', "
  "theme_color: '#2068FF', background_color: '#ffffff', "
  "display: 'standalone', orientation: 'portrait', "
  "icons: [{src: icon-192.png, sizes: '192x192'}, {src: icon-512.png, sizes: '512x512'}] }. "
  "Add <link rel='manifest' href='/manifest.json'> to index.html. "
  "Create icons: generate from Intercom logo or MiroFish brand mark. "
  "Add apple-touch-icon and apple-mobile-web-app meta tags for iOS.")

t(92, "Add install prompt for PWA",
  "Create frontend/src/components/common/InstallPrompt.vue — PWA install banner. "
  "Listen for 'beforeinstallprompt' event. Show banner: 'Install MiroFish GTM Demo for quick access'. "
  "Install button that triggers the browser's install flow. "
  "Dismiss button that hides for 7 days (localStorage). "
  "Show on bottom of screen, above system status bar. "
  "After install: update UI to show 'Running as installed app' in settings.")

t(92, "Configure PWA update notifications",
  "Update the service worker registration to handle updates: "
  "When new version detected: show banner 'Update available — click to refresh'. "
  "On click: skipWaiting on new service worker, reload page. "
  "On automatic update: show brief toast notification. "
  "Version tracking: include build hash in service worker cache name.")

t(93, "Create 3D force-directed graph with Three.js",
  "Create frontend/src/components/visualization/Graph3D.vue — Three.js 3D force graph. "
  "Install: cd frontend && pnpm add three @types/three. "
  "Render agent network as a 3D force-directed graph: "
  "Nodes: spheres colored by role, sized by influence. "
  "Edges: lines colored by sentiment, thickness by interaction count. "
  "Camera controls: orbit (mouse drag), zoom (scroll), pan (right-click drag). "
  "Node labels: text sprites floating above nodes. "
  "Click node: highlight connections. Double-click: focus camera. "
  "Performance: limit to 50 nodes and 200 edges for smooth rendering.")

t(93, "Add 3D graph animations",
  "Update Graph3D.vue with animations: "
  "Node pulse: nodes pulse when an agent sends a message. "
  "Edge particle flow: animated particles traveling along edges showing information flow. "
  "Camera auto-rotation: slow orbit for idle/demo mode. "
  "Zoom transitions: smooth camera movement when clicking nodes. "
  "Graph layout animation: nodes settle into positions over 2 seconds on mount. "
  "Use requestAnimationFrame for rendering loop.")

t(93, "Add 3D graph to simulation workspace",
  "Integrate Graph3D as a tab option in the simulation workspace: "
  "New tab: '3D Network' alongside existing 2D network view. "
  "Synchronized with timeline scrubber: graph state updates as round changes. "
  "Toggle between 2D and 3D with a view mode selector. "
  "3D graph receives the same data as the 2D AgentNetworkGraph component.")

t(94, "Create real-time collaboration simulation display",
  "Create frontend/src/components/simulation/CollaborationIndicator.vue — shows simulated real-time collaboration. "
  "Display: '3 agents are currently discussing...' with animated typing indicators. "
  "Show agent avatars in a connected bubble layout, with animated thought bubbles. "
  "Simulate the feel of watching a real team collaboration in real-time. "
  "Use for demo effect: makes the simulation feel alive and engaging. "
  "Works with both WebSocket (real-time) and replay mode.")

t(94, "Build multi-user presence simulation",
  "Create frontend/src/components/common/PresenceIndicator.vue — simulates multiple users viewing. "
  "Shows small avatar circles of 'other viewers' in the top-right of the page. "
  "Generates 2-3 fake viewer names from Intercom team members. "
  "Hover: shows 'Alice is viewing the Dashboard' tooltip. "
  "Animated: viewers occasionally change pages. "
  "This is for demo effect only — not real multi-user functionality. "
  "Toggle in settings: 'Show Collaboration Presence' (default on for demo).")

t(95, "Final comprehensive QA pass",
  "Comprehensive quality assurance check: "
  "1) Every page loads without console errors. "
  "2) Every chart renders with data (no empty SVGs or broken charts). "
  "3) Every navigation link works. "
  "4) Demo mode works end-to-end: simulation runs, data shows, reports generate. "
  "5) Dark mode works on every page (no white-on-white or black-on-black). "
  "6) All form inputs have labels and are accessible. "
  "7) No TODO or FIXME comments in production code. "
  "8) No hardcoded localhost URLs in production builds. "
  "9) Brand colors consistent throughout. "
  "10) All tests pass (frontend + backend). "
  "Document findings in docs/final-qa.md. Fix any critical issues. "
  "This is the final task — the app should be presentation-ready after this.")

# Write output
if __name__ == "__main__":
    print(f"Generated {len(NEW_TASKS)} tasks for groups 62-95")
    with open("tmp/tasks_62_95.json", "w") as f:
        json.dump(NEW_TASKS, f, indent=2)
    print(f"Saved to tmp/tasks_62_95.json")
