# Architecture

> Last updated: 2026-07-26  
> Status: 像素风桌宠生成链路已接入 Cloudflare Worker 代理（上游已从 OpenAI 切换为 Agnes AI）；桌面端不持有 API Key。

## File Purposes

| File | Responsibility |
|---|---|
| `src/main.py` | Entry point: QApplication, QSystemTrayIcon, creates PetWindow + service graph + management MainWindow |
| `src/pet_window.py` | PetWindow (QWidget): transparent overlay, alpha hit-test mask, event handlers, drag/drop, scroll-wheel resize, hunger controls, pixel-art mode delegation |
| `src/state_machine.py` | PetStateMachine: pure logic — reads cursor state → emits state transitions (IDLE/FOLLOWING/RUNNING/EXCITED/DRAGGED) |
| `src/pet_renderer.py` | PetRenderer: QLabel + QPixmap/QMovie for static/GIF display, per-state visual transforms, variable-size rendering, nearest-neighbour scaling when `pixel_art_mode=True` |
| `src/mouse_tracker.py` | MouseTracker: QTimer (16ms) polling QCursor.pos(), computes speed, delta, still_duration |
| `src/pet_status.py` | PetStatusEngine: hunger (0-100) with 10s decay timer, normal/foraging state, feed_pet() restores 30 hunger |
| `src/config.py` | Config: QSettings("DesktopPet", "settings") wrapper — save/load position (pet/x, pet/y), scale (pet/scale), and image path (pet/image_path) |
| `src/image_processor.py` | BackgroundRemover QThread wrapping rembg; PixelArtGenerator local Pillow fallback (downsample + palette + NEAREST upscale) |
| `src/services/env_config.py` | Reads `.env`/environment variables. Desktop app stores only `PIXEL_PROXY_URL`; OpenAI API Key is not read client-side. |
| `src/services/generation_service.py` | OpenAIPixelGenerator QThread: calls Cloudflare Worker `/generate`, validates returned image bytes, saves temp file, runs rembg second pass, emits finished/error. |
| `src/services/ai_service.py` | AIService factory: remove_background() returns BackgroundRemover; generate_pixel_art() selects Worker proxy when `PIXEL_PROXY_URL` exists, otherwise local PixelArtGenerator fallback. |
| `src/services/image_service.py` | Image utilities: format validation, import into managed storage, output-path generation for no-bg and pixel outputs. |
| `src/services/database_service.py` | Persistence facade: QSettings + SQLite DatabaseManager + app data directories (`images/original`, `images/processed`, `images/generated`). |
| `src/services/pet_service.py` | Pet lifecycle service: create/switch/delete pets, sync active image to PetWindow and QSettings, apply pixel-art scaling mode. |
| `src/ui/upload_page.py` | Create-pet flow: mode selector (remove background / pixel art), upload preview, generation state, result preview, duplicate-submit guard, cancel-on-reset/hide. |
| `src/ui/pet_management_page.py` | Saved pet grid with switch/delete actions. |
| `proxy/worker.js` | Cloudflare Worker proxy: receives multipart `image`, converts to base64 Data URI, calls Agnes AI Images Generations API (`agnes-image-2.1-flash`), returns generated PNG bytes. Holds API Key only via Worker secret. |
| `proxy/wrangler.toml` | Cloudflare Worker deployment config. |

## Data Flow

### Desktop interaction loop

```
MouseTracker (cursor pos, speed, still_duration)
       │
       ▼
StateMachine (IDLE / FOLLOWING / RUNNING / EXCITED / DRAGGED)
       │
       ├──► PetWindow.update_position() ──► lerp: pet += (target - pet) * stiffness * dt
       │         │
       │         ▼
       └──► PetRenderer.set_state_visual() ──► QLabel transform / scale / animation

PetStatusEngine (hunger 0-100, 10s decay timer)
       │
       ├──► update_state() ──► hunger≥20 → "normal", hunger<20 → "foraging"
       │         │
       │         ▼
       └──► [状态变更] / [喂食] ──► print to terminal (debug)

PetWindow.feed_requested (double-click / feed button) ──► PetStatusEngine.feed_pet()
```

### Create pet: original background removal

```
UploadPage
  ├── import uploaded image via ImageService.import_image()
  ├── AIService.remove_background()
  │     └── BackgroundRemover (rembg QThread)
  ├── preview processed PNG
  └── PetService.create_pet_from_image(is_pixel_art=False)
        ├── DatabaseService.add_pet()
        ├── PetWindow.set_image()
        └── QSettings pet/image_path
```

### Create pet: pixel-art generation

```
UploadPage
  ├── import uploaded image via ImageService.import_image()
  ├── AIService.generate_pixel_art()
  │     ├── if PIXEL_PROXY_URL configured:
  │     │     OpenAIPixelGenerator
  │     │       ├── POST {PIXEL_PROXY_URL}/generate (multipart image)
  │     │       ├── validate returned image magic bytes
  │     │       ├── save temp image
  │     │       ├── rembg second pass → transparent PNG
  │     │       └── finished(output_path)
  │     └── else:
  │           PixelArtGenerator local fallback
  ├── preview generated PNG
  └── PetService.create_pet_from_image(is_pixel_art=True)
        ├── DatabaseService.add_pet()
        ├── PetWindow.set_image()
        ├── PetWindow.pixel_art_mode = True
        └── QSettings pet/image_path
```

### Cloudflare Worker proxy

```
Desktop app (no API key)
  └── POST /generate multipart image
        ▼
Cloudflare Worker (OPENAI_API_KEY secret → Agnes API Key)
  ├── validate image field and size <= 10 MB
  ├── convert image to base64 Data URI
  ├── POST https://apihub.agnes-ai.com/v1/images/generations (JSON)
  │     ├── model = agnes-image-2.1-flash
  │     ├── image = ["data:image/...;base64,..."]
  │     ├── prompt = server-side pixel-pet prompt
  │     └── extra_body.response_format = b64_json
  ├── decode b64_json image
  ├── validate returned image magic bytes
  └── return image/png bytes
```

## State Machine

See [game-design-document.md](game-design-document.md) §4.3 for the full state diagram and transition rules.

## Config Schema

```
QSettings("DesktopPet", "settings")
  ├── pet/image_path   : str   — path to user's active pet image file
  ├── pet/x            : int   — window X position
  ├── pet/y            : int   — window Y position
  └── pet/scale        : float — size multiplier (default 1.0, base=128px)
```

## Local `.env` Schema

```
PIXEL_PROXY_URL : str — Cloudflare Worker base URL, e.g.
                      https://desktop-pet-pixel-proxy.<subdomain>.workers.dev
```

No OpenAI API Key is stored in the desktop app `.env`. The key is stored as the Worker secret `OPENAI_API_KEY` via `wrangler secret put OPENAI_API_KEY`.

## SQLite Database Schema

SQLite database path: `%APPDATA%/DesktopPet/desktop_pet.db` on Windows.

```sql
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS images (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path   TEXT    NOT NULL,
    original_name   TEXT    NOT NULL DEFAULT '',
    format          TEXT    NOT NULL DEFAULT '',
    processed_path  TEXT,
    create_time     TEXT    DEFAULT (datetime('now','localtime')),
    status          TEXT    DEFAULT 'active',
    is_used         INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pets (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id             INTEGER,
    pet_name             TEXT    NOT NULL,
    pet_path             TEXT    NOT NULL,
    original_image_path  TEXT    DEFAULT '',
    scale                REAL    DEFAULT 1.0,
    create_time          TEXT    DEFAULT (datetime('now','localtime')),
    is_active            INTEGER DEFAULT 0,
    is_pixel_art         INTEGER DEFAULT 0,
    FOREIGN KEY (image_id) REFERENCES images(id)
);
```

Migration behavior: `DatabaseManager._init_schema()` runs `ALTER TABLE pets ADD COLUMN is_pixel_art INTEGER DEFAULT 0` and ignores the “column already exists” error. Existing pets therefore remain readable and default to normal rendering.

## Size / Scale System

- **Base size:** 128×128 px at scale = 1.0
- **Range:** 32–512 px (scale 0.25× – 4.0×)
- **Control:** mouse scroll wheel (±10% per step)
- **Persistence:** saved as `pet/scale` in QSettings; restored on launch
- **Pixel art rendering:** `PetRenderer.pixel_art_mode=True` uses `Qt.FastTransformation` (nearest-neighbour) to avoid blur. Normal pets continue using smooth scaling.
