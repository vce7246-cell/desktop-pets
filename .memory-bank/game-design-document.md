# Game Design Document: Desktop Pet App

> **Version:** 0.1.0  
> **Date:** 2026-07-03  
> **Status:** Pre-production

---

## 1. Elevator Pitch

A lightweight, cross-platform desktop companion that lives on top of your screen. Users upload any image or GIF as their pet — it floats above all windows, follows the mouse cursor with lifelike movement, and reacts to cursor speed and proximity with distinct animation states. Zero UI clutter: no window borders, no background, no taskbar footprint beyond a tiny tray icon.

---

## 2. Target Audience

| Segment | Motivation |
|---|---|
| **Casual users** | Cute desktop decoration, stress relief |
| **Streamers / content creators** | On-screen mascot that reacts to their cursor movements on stream |
| **Customization enthusiasts** | Upload their own art, OCs, or brand mascots as pets |
| **Kids / families** | Simple virtual pet without complex mechanics |

---

## 3. Core Pillars (Experience Goals)

| Pillar | Description |
|---|---|
| **Invisible shell** | The window does not look like a window. No borders, no background, no title bar. Only the pet is visible. |
| **Always present** | Always-on-top, always visible. The pet feels like part of the desktop, not another application. |
| **Reactive companion** | The pet responds to mouse movement — following, fleeing, watching. It feels alive, not robotic. |
| **Zero friction** | No onboarding. Drag in an image, it becomes your pet. Right-click the tray icon to change or quit. |

---

## 4. Feature Breakdown

### 4.1 Desktop Pet Window

| Requirement | Implementation Notes |
|---|---|
| Always-on-top | `WS_EX_TOPMOST` (Win) / `NSWindow.level = .floating` (macOS) |
| Transparent background | Chroma-key / per-pixel alpha blending |
| Borderless | `WS_POPUP` (Win) / `NSWindow.StyleMask.borderless` (macOS) |
| Click-through on transparent areas | `WS_EX_TRANSPARENT` (Win) / `NSTrackingArea` + hit-test override (macOS) |
| No taskbar entry | Tray icon only; hide from Alt+Tab |

### 4.2 Pet Image Upload

- **Supported formats:** PNG, JPG, GIF, WebP
- **Upload methods:**
  - Drag & drop an image file onto the pet
  - Right-click tray icon → "Change Pet…" → file picker dialog
- **GIF handling:** Play animated GIFs in a loop. Static images display as-is.
- **Size normalization:** Images auto-scale to a default pet size (~128×128 px at 1x). User can resize via tray menu or scroll wheel.
- **Persistence:** Last-used image path stored in local config. Loads automatically on next launch.

### 4.3 Mouse Interaction & Animation States

The pet has a **state machine** driven by cursor movement:

```
                  ┌──────────────┐
     mouse fast   │              │  mouse stops
   ┌─────────────▶│   RUNNING    │──────────────┐
   │              │              │              │
   │              └──────┬───────┘              │
   │        mouse slows  │                      ▼
   │                     │              ┌──────────────┐
   │                     └──────────────▶│              │
   │                                    │    IDLE      │
┌──┴───────────┐                       │  (breathing,  │
│              │     mouse near pet    │  blinking)    │
│   FOLLOWING  │◀──────────────────────│              │
│  (tether)    │                       └──────┬───────┘
│              │                              │
└──────┬───────┘                     mouse near pet
       │                                   │
       │  mouse far or fast                ▼
       │                          ┌──────────────┐
       └─────────────────────────▶│              │
                                  │   EXCITED    │
                                  │ (bounce,     │
                                  │  heart eyes) │
                                  └──────────────┘
```

#### State Definitions

| State | Trigger | Behavior | Visual |
|---|---|---|---|
| **IDLE** | Mouse stationary for >2s | Pet stays in place. Subtle bob/breath animation via CSS or frame cycling. | Slight scale oscillation (±2%), slow blink overlay |
| **FOLLOWING** | Mouse moving slowly (< 300 px/s) | Pet window lerps toward cursor position. Feels like a gentle tether — not locked to cursor. | "Walking" or "floating" animation if GIF has directional frames |
| **RUNNING** | Mouse moving fast (> 600 px/s) | Pet trails behind cursor with faster lerp, slight overshoot. | "Running" or "panicked" animation; motion blur or speed lines |
| **EXCITED** | Cursor within 150px of pet center | Pet faces cursor, bounces or pulses. | Bounce animation, "heart" or "!" emotes, scale up 10% |
| **DRAGGED** | User clicks non-transparent pet area | Pet attaches to cursor. Released on click. | Slight squash/stretch while dragged |

#### Lerp / Tether Math

```
targetPosition = cursorPosition + offset
petPosition += (targetPosition - petPosition) * stiffness * deltaTime
```

- `stiffness` varies by state: FOLLOWING = 3.0, RUNNING = 1.5 (laggier), IDLE = 0 (static)
- `offset` is the pet's "leash point" — configurable (default: pet sits slightly below-right of cursor)

### 4.4 Tray Icon & Minimal UI

| Action | Access |
|---|---|
| Change pet image | Tray menu → "Change Pet…" |
| Resize pet | Tray menu → "Size" submenu (0.5×, 1×, 1.5×, 2×) |
| Toggle always-on-top | Tray menu → "Always on Top" (checkable) |
| Quit | Tray menu → "Quit" |
| Drag-to-reposition | Click & drag pet (non-transparent area) |

No main window, no settings dialog in v1 — just the tray menu.

---

## 5. Technical Design

### 5.1 Recommended Tech Stack

#### Primary Recommendation: **Tauri (Rust + Web Frontend)**

| Layer | Technology | Rationale |
|---|---|---|
| **Runtime** | [Tauri 2.x](https://v2.tauri.app/) | Cross-platform (Win/Mac/Linux), binary size ~3-5 MB, memory ~30-50 MB |
| **Backend** | Rust | System-level window control (transparency, top-most, click-through, global mouse tracking) |
| **Frontend** | HTML + CSS + vanilla JS (or Preact) | Pet rendering via `<img>` / `<canvas>`, CSS animations for idle/bounce states |
| **Config** | JSON file in app data dir | Stores last pet image path, size, position |

**Why Tauri over alternatives:**

| Alternative | Verdict |
|---|---|
| **Electron** | ~150 MB RAM, 200+ MB disk. Overkill for a single-image window. Rejected. |
| **Python + PyQt6** | Faster dev, but 60-80 MB RAM, packaging is fragile (PyInstaller). Good for prototyping. |
| **C# + WPF** | Windows-only. Fails cross-platform requirement. |
| **.NET MAUI** | Cross-platform but immature on desktop. Transparency APIs are limited. |
| **Unity / Godot** | Game engines are 50-100+ MB binaries for what is essentially one sprite. Overkill. |

#### Fallback (Rapid Prototyping): **Python + PyQt6**

If Rust/Tauri's learning curve is a blocker, PyQt6 provides:
- `Qt.WindowStaysOnTopHint` for always-on-top
- `Qt.FramelessWindowHint` + `setAttribute(Qt.WA_TranslucentBackground)` for borderless transparency
- `setMask()` with the alpha channel for click-through
- `QCursor.pos()` for global mouse tracking (via a 16ms timer)
- PyInstaller for single-file distribution (~40 MB)

### 5.2 Architecture Overview (Tauri)

```
┌─────────────────────────────────────────┐
│              Tauri (Rust)               │
│                                         │
│  ┌───────────┐  ┌────────────────────┐  │
│  │  Window    │  │  Global Mouse Hook │  │
│  │  Manager   │  │  (mouce crate or   │  │
│  │  (tauri    │  │   platform-native) │  │
│  │  window)   │  │                    │  │
│  └─────┬─────┘  └────────┬───────────┘  │
│        │                 │              │
│        ▼                 ▼              │
│  ┌────────────────────────────────────┐  │
│  │         IPC Bridge (invoke)        │  │
│  └────────────────┬───────────────────┘  │
│                   │                      │
└───────────────────┼──────────────────────┘
                    │
┌───────────────────┼──────────────────────┐
│    WebView (HTML/CSS/JS)                 │
│                   ▼                      │
│  ┌────────────────────────────────────┐  │
│  │         State Machine              │  │
│  │  (IDLE / FOLLOW / RUN / EXCITED)   │  │
│  └────────────────┬───────────────────┘  │
│                   │                      │
│  ┌────────────────▼───────────────────┐  │
│  │         Render Layer               │  │
│  │  <img> or <canvas> + CSS anims     │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### 5.3 Global Mouse Tracking Strategy

| OS | Approach |
|---|---|
| **Windows** | `SetWindowsHookEx(WH_MOUSE_LL, ...)` or Tauri's global shortcut plugin |
| **macOS** | `CGEventTap` or `NSEvent.addGlobalMonitorForEvents` |
| **Linux** | X11 `XQueryPointer` or Wayland protocol (limited; may need polling fallback) |

Polling fallback: 60 Hz `requestAnimationFrame` loop querying cursor position via platform API. Acceptable CPU cost (~1-2%).

### 5.4 Window Transparency & Hit-Testing

```
Window creation flags:
  - decorations: false
  - transparent: true
  - always_on_top: true
  - skip_taskbar: true
  - visible_on_all_workspaces: true (optional)

Hit-testing:
  - Default: click passes through window
  - Only non-transparent pixels of the pet image block clicks
  - Implemented via per-pixel alpha check on mousedown
```

---

## 6. Art & Asset Requirements

### 6.1 User-Provided Pet Images

| Property | Value |
|---|---|
| Recommended resolution | 128×128 to 256×256 px |
| Supported formats | PNG, JPG, GIF, WebP |
| Max file size | 10 MB (warn above) |
| Aspect ratio | Any; pet is contained within bounds, not cropped |

### 6.2 Built-in Default Pet (v1)

A simple default pet is shipped so the app works out of the box:
- A cute blob/cat silhouette in PNG format
- 2-3 idle frames (blinking animation)
- Stored as embedded assets, no external file dependency

### 6.3 Animation Notes

- For **GIF pets:** the GIF's natural frames serve as the animation. State transitions can be expressed via CSS transform overlays (scale, rotate, translate) on top of the GIF — no need for per-state sprite sheets.
- For **static image pets:** CSS animations simulate breathing (scale pulse), bouncing (translateY oscillation), and blinking (a semi-transparent "eyelid" div that animates down/up).

---

## 7. Interaction Design Summary

```
┌─────────────────────────────────────────────────────────┐
│  Cursor Behavior          │  Pet Response               │
├───────────────────────────┼─────────────────────────────┤
│  Stationary (>2s)         │  IDLE: gentle breathing     │
│  Slow move (<300 px/s)    │  FOLLOW: lerped tether      │
│  Fast move (>600 px/s)    │  RUN: trailing with lag     │
│  Approaches pet (<150px)  │  EXCITED: bounce toward     │
│  Leaves pet vicinity      │  Return to FOLLOW/IDLE      │
│  Clicks pet body          │  Pick up & drag             │
│  Clicks transparent area  │  Passes through to app below│
│  Right-clicks pet         │  Tray context menu          │
│  Scroll wheel on pet      │  Resize pet (±10% per tick) │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Development Roadmap

### Milestone 1 — "Hello, World" (v0.1)
- [ ] Tauri project scaffold with transparent, borderless, always-on-top window
- [ ] Display a hardcoded PNG sprite on screen
- [ ] Tray icon with "Quit" menu item
- [ ] Verify click-through on transparent areas

### Milestone 2 — "It Moves" (v0.2)
- [ ] Global mouse position polling (60 Hz)
- [ ] FOLLOW state: window lerps toward cursor
- [ ] RUN state: faster cursor = laggier follow
- [ ] IDLE state: stationary when cursor is still

### Milestone 3 — "It Feels Alive" (v0.3)
- [ ] EXCITED state: proximity detection
- [ ] CSS animation layer for idle breathing / excited bounce
- [ ] State machine with smooth transitions (no snapping)
- [ ] Drag-to-reposition (click & drag pet body)

### Milestone 4 — "Make It Yours" (v0.4)
- [ ] File picker for custom pet image (tray menu → "Change Pet…")
- [ ] Drag & drop image onto pet to replace
- [ ] GIF animation support (loop playback)
- [ ] Persist last image path + settings to config file

### Milestone 5 — "Ship It" (v1.0)
- [ ] Resize controls (tray menu + scroll wheel)
- [ ] Default built-in pet asset
- [ ] Cross-platform packaging (Windows: .msi/.exe, macOS: .dmg)
- [ ] Basic error handling (unsupported formats, missing files)
- [ ] README with build instructions

---

## 9. Open Questions & Decisions

| # | Question | Status |
|---|---|---|
| 1 | Should multiple pets be supported simultaneously? | **Defer to v2.** v1 = single pet. |
| 2 | Should the pet "walk" around the screen on its own when idle too long? | **Defer to v2.** Autonomous wandering adds complexity (collision with screen edges, window icons). |
| 3 | Should there be sound effects? | **No for v1.** Keeps binary small and avoids audio permission issues. |
| 4 | Tauri vs PyQt6 — which to use? | **Tauri recommended** for production; PyQt6 acceptable for prototype. Decision pending developer preference. |
| 5 | Linux support in v1? | **Best-effort.** Primary targets are Windows and macOS. Wayland transparency is still maturing. |

---

## 10. Success Criteria (v1.0)

1. App launches and displays a pet image floating above all windows within 2 seconds.
2. CPU usage < 5% when idle, < 10% during mouse following.
3. Memory usage < 80 MB steady-state.
4. Pet follows cursor with visibly smooth motion (no jitter at 60 Hz).
5. Clicking transparent areas around the pet passes clicks through to underlying windows.
6. User can change pet image via tray menu or drag-and-drop.
7. GIF pets animate; static pets render correctly.
8. Settings persist across app restarts.
