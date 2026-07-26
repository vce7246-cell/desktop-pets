# Progress Tracking

> Last updated: 2026-07-26

## Current Status: 像素风生成链路完整可用（上游已切换为 Agnes AI）

---

## 🆕 像素风桌宠生成

- [x] 创建桌宠页支持两种模式：原图去背景 / 像素风生成
- [x] 像素风流程：上传 → 原图预览 → 生成中 → 结果预览 → 重新生成 / 设为桌宠
- [x] 生成过程中禁止重复提交
- [x] 上传新图片会清空上一次结果
- [x] 失败时保留原图，允许重新生成
- [x] 服务层隔离：`AIService.generate_pixel_art()` + `OpenAIPixelGenerator`
- [x] 无代理配置时使用本地 Pillow 像素化回退
- [x] 有 `PIXEL_PROXY_URL` 时通过 Cloudflare Worker 代理调用 AI 图片接口
- [x] 桌面端不保存 API Key；Key 存在 Worker secret `OPENAI_API_KEY`
- [x] 生成结果保存为现有桌宠资源，复用桌宠列表/切换逻辑
- [x] `pets.is_pixel_art` 字段向后兼容；旧宠物默认普通渲染
- [x] 像素风桌宠使用 nearest-neighbour 缩放，普通桌宠不受影响
- [x] 上游已从 OpenAI 切换为 Agnes AI (`agnes-image-2.1-flash`)，Worker 已重新部署
- [x] 真实代理生成验证通过

---

## 🆕 状态管理引擎 (PetStatusEngine)

- [x] `src/pet_status.py` — PetStatusEngine 类：hunger (0-100), state (normal/foraging)
- [x] QTimer 每 10s：hunger -= 2 → update_state()
- [x] `feed_pet()`: hunger += 30 (max 100) → update_state() → print
- [x] 双击宠物 → feed_requested 信号 → feed_pet()
- [x] 状态变更时终端打印 `[状态变更]` / `[喂食]`

---

## Phase 1: Project Skeleton

- [x] Step 1.1 — Create virtual environment and install dependencies
- [x] Step 1.2 — Create directory structure and empty modules
- [x] Step 1.3 — Skeleton main.py: QApplication starts and exits cleanly

## Phase 2: Invisible Pet Window

- [x] Step 2.1 — Transparent, borderless, always-on-top window
- [x] Step 2.2 — Click-through on transparent areas
- [x] Step 2.3 — Window closes cleanly via Ctrl+C

## Phase 3: Render the Pet Image

- [x] Step 3.1 — Display a static PNG on the transparent window
- [x] Step 3.2 — Click-through: only transparent pixels pass clicks

## Phase 4: Mouse Tracking

- [x] Step 4.1 — Poll global cursor position at 60 Hz
- [x] Step 4.2 — Compute cursor speed (pixels per second)

## Phase 5: State Machine

- [x] Step 5.1 — Define the 4 base states and transitions
- [x] Step 5.2 — Wire MouseTracker into StateMachine
- [x] Step 5.3 — Track mouse-still duration

## Phase 6: Pet Motion

- [x] Step 6.1 — Implement lerp-based window movement
- [x] Step 6.2 — Motion feels smooth (no jitter)
- [x] Step 6.3 — Apply per-state visual feedback

## Phase 7: Basic Interaction

- [x] Step 7.1 — Click-and-drag to reposition pet
- [x] Step 7.2 — System tray icon with "Quit"
- [x] Step 7.3 — Pet window hides on Quit with no ghost process

## Phase 8: Configuration Persistence

- [x] Step 8.1 — Save and load pet position on exit/startup
- [x] Step 8.2 — Save and load pet image path

## Phase 9: Change Pet Image (Tray Menu)

- [x] Step 9.1 — File picker via tray menu "更换宠物"

## Phase 10: Drag & Drop Image

- [x] Step 10.1 — Accept image file drops on pet window

## Phase 11: Scroll Wheel Resize

- [x] Step 11.1 — Resize pet via mouse scroll wheel

## Phase 12: PyInstaller Packaging

- [ ] Step 12.1 — Single-file executable build
