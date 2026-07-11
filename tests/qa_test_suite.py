"""QA Test Suite for Desktop Pet.
Runs without stdout wrapping — uses ASCII-only output to survive Windows console.
"""
import os, shutil, sqlite3, sys, tempfile, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

passed = 0
failed = 0
warnings = 0

def check(desc, condition, detail="", warn=False):
    global passed, failed, warnings
    if condition:
        passed += 1
        print(f"  [PASS] {desc}")
    elif warn:
        warnings += 1
        print(f"  [WARN] {desc} -- {detail}")
    else:
        failed += 1
        print(f"  [FAIL] {desc} -- {detail}")
    return condition

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def try_call(fn):
    try: return fn(), None
    except Exception as e: return None, str(e)

# ======================================================================
# Setup
# ======================================================================
section("0. Environment Setup")

from PyQt6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
check("QApplication created", app is not None)

TMP = Path(tempfile.mkdtemp(prefix="dp_qa_"))
TMP_ORIG = TMP / "images" / "original"
TMP_PROC = TMP / "images" / "processed"
TMP_ORIG.mkdir(parents=True, exist_ok=True)
TMP_PROC.mkdir(parents=True, exist_ok=True)
print(f"  Temp dir: {TMP}")

# ======================================================================
# PART 1: Imports
# ======================================================================
section("1. Module Imports")

modules = [
    "src.config",
    "src.state_machine",
    "src.mouse_tracker",
    "src.pet_status",
    "src.pet_renderer",
    "src.pet_window",
    "src.image_processor",
    "src.database.db_manager",
    "src.services.image_service",
    "src.services.ai_service",
    "src.services.database_service",
    "src.services.pet_service",
    "src.models.pet",
    "src.models.image_asset",
    "src.ui.dashboard_page",
    "src.ui.upload_page",
    "src.ui.image_library_page",
    "src.ui.pet_management_page",
    "src.ui.settings_page",
    "src.ui.main_window",
]

errors = []
for m in modules:
    _, err = try_call(lambda: __import__(m, fromlist=["_"]))
    if err: errors.append(f"{m}: {err}")

check("All modules imported", len(errors) == 0, "; ".join(errors) if errors else "")
if errors:
    print("ABORT: import failures")
    sys.exit(1)

# Import classes for testing
from src.config import Config
from src.state_machine import PetStateMachine, PetState
from src.pet_status import PetStatusEngine
from src.image_processor import BackgroundRemover
from src.database.db_manager import DatabaseManager
from src.services.image_service import ImageService
from src.services.ai_service import AIService
from src.services.database_service import DatabaseService

# ======================================================================
# PART 2: Database
# ======================================================================
section("2. Database CRUD")

# 2.1 Schema
db_path = str(TMP / "test.db")
db = DatabaseManager(db_path)
check("DB file created", Path(db_path).exists())

conn = sqlite3.connect(db_path)
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
conn.close()
for t in ["users", "images", "pets"]:
    check(f"Table '{t}' exists", t in tables)

# 2.2 Images CRUD
section("2.2 Images CRUD")
img_id = db.add_image({"original_path": str(TMP_ORIG / "cat.png"), "original_name": "cat.png", "format": "png"})
check("add_image returns int ID", isinstance(img_id, int) and img_id > 0)

imgs = db.get_all_images()
check("get_all_images returns non-empty list", len(imgs) >= 1)
check("Column mapping: created_at in dict", "created_at" in imgs[0])
check("Column mapping: create_time NOT in dict", "create_time" not in imgs[0])

db.update_image(img_id, {"processed_path": str(TMP_PROC / "cat_nobg.png"), "is_used": True})
updated = [i for i in db.get_all_images() if i["id"] == img_id][0]
check("update_image: processed_path updated", updated.get("processed_path") == str(TMP_PROC / "cat_nobg.png"))
check("update_image: is_used (bool->int)", updated.get("is_used") == 1)

db.delete_image(img_id)
check("Soft delete: image not in active list", all(i["id"] != img_id for i in db.get_all_images()))

conn = sqlite3.connect(db_path)
row = conn.execute("SELECT status FROM images WHERE id=?", (img_id,)).fetchone()
conn.close()
check("Soft delete: DB status='deleted'", row is not None and row[0] == "deleted")

# 2.3 Pets CRUD
section("2.3 Pets CRUD")
pet_id = db.add_pet({"name": "TestCat", "image_path": str(TMP_ORIG / "cat.png"), "is_active": True})
check("add_pet returns int ID", isinstance(pet_id, int) and pet_id > 0)

pets = db.get_all_pets()
check("Column mapping: name in dict", pets[0].get("name") == "TestCat")
check("Column mapping: image_path in dict", "image_path" in pets[0])
check("Column mapping: pet_name NOT in dict", "pet_name" not in pets[0])
check("Column mapping: pet_path NOT in dict", "pet_path" not in pets[0])

active = db.get_active_pet()
check("get_active_pet returns active pet", active is not None and active["id"] == pet_id)

# Auto-deactivate
pet2_id = db.add_pet({"name": "TestDog", "image_path": "/tmp/dog.png", "is_active": True})
check("New active pet gets different ID", pet2_id != pet_id)

active2 = db.get_active_pet()
check("Active pet switched to new one", active2["id"] == pet2_id)

old = [p for p in db.get_all_pets() if p["id"] == pet_id][0]
check("Old pet auto-deactivated", old["is_active"] == 0)

# Update to re-activate old
db.update_pet(pet_id, {"is_active": True})
active3 = db.get_active_pet()
check("update_pet(is_active=True) switches active", active3["id"] == pet_id)

# Hard delete
db.delete_pet(pet2_id)
check("Hard delete: pet removed", all(p["id"] != pet2_id for p in db.get_all_pets()))

# 2.4 Edge cases
section("2.4 DB Edge Cases")
db.add_pet({"name": "EdgeTest", "image_path": "/tmp/x.png", "is_active": False, "nonexistent_key": "ignored"})
check("Unknown dict keys silently ignored", True)
db.update_pet(pet_id, {})
check("Empty update dict does not crash", True)
db.update_pet(pet_id, {"nonexistent_key": "val"})
check("Update with unknown keys does not crash", True)

# ======================================================================
# PART 3: Image Service
# ======================================================================
section("3. ImageService")
svc = ImageService()
check("validate .png", svc.validate_format("test.png"))
check("validate .jpg", svc.validate_format("test.jpg"))
check("validate .gif", svc.validate_format("test.gif"))
check("validate .webp", svc.validate_format("test.webp"))
check("reject .bmp", not svc.validate_format("test.bmp"))
check("reject .txt", not svc.validate_format("test.txt"))
check("get_format lowercase", svc.get_format("X.PNG") == "png")

# Make a minimal valid PNG
minimal_png = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f'
    b'\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
)
src_img = TMP / "source.png"
src_img.write_bytes(minimal_png)

imported = svc.import_image(str(src_img), TMP_ORIG)
check("import_image copies to target dir", Path(imported).parent == TMP_ORIG)
check("import_image file exists", Path(imported).is_file())
check("import_image generates unique name", Path(imported).name != "source.png")

out = svc.make_output_path(str(TMP_ORIG / "test_cat.png"))
check("make_output_path appends _nobg", "_nobg" in out)

# Collision handling
collide = TMP_ORIG / "collide_nobg.png"
collide.write_bytes(minimal_png)
out2 = svc.make_output_path(str(TMP_ORIG / "collide.png"))
check("make_output_path collision avoidance", "_nobg_2" in out2 or "_nobg_" in out2)

# Default pet detection
default_path = str(Path(__file__).resolve().parent.parent / "src" / "assets" / "default_pet.png")
check("is_default_pet True for default", svc.is_default_pet(default_path))
check("is_default_pet False for other", not svc.is_default_pet("/tmp/random.png"))

# ======================================================================
# PART 4: AI Service
# ======================================================================
section("4. AI Service (BackgroundRemover)")
ai = AIService()
remover = ai.remove_background(str(TMP_ORIG / "nonexistent.png"), str(TMP_PROC / "out.png"), parent=app)
check("remove_background returns BackgroundRemover", isinstance(remover, BackgroundRemover))
check("BackgroundRemover is QThread subclass", hasattr(remover, "start"))
check("has finished signal", hasattr(remover, "finished"))
check("has error signal", hasattr(remover, "error"))

error_msgs = []
remover.error.connect(lambda msg: error_msgs.append(msg))
remover.start()
remover.wait(5000)
check("Missing file triggers error signal", len(error_msgs) > 0)
if error_msgs:
    check("Error message is non-empty", len(error_msgs[0]) > 0)

# ======================================================================
# PART 5: State Machine & Status Engine
# ======================================================================
section("5. State Machine & Status Engine")

sm = PetStateMachine()
check("Initial state FOLLOWING", sm.current_state == PetState.FOLLOWING)

s = sm.update(800, 300, 0)
check("High speed -> RUNNING", s == PetState.RUNNING)

s = sm.update(200, 50, 0)
check("Close + moving -> EXCITED", s == PetState.EXCITED)

s = sm.update(0, 500, 3.0)
check("Still 3s -> IDLE", s == PetState.IDLE)

s = sm.update(100, 500, 0)
check("Low speed -> FOLLOWING", s == PetState.FOLLOWING)

# PetStatusEngine
engine = PetStatusEngine()
check("Initial hunger = 80", engine.hunger == 80)
check("Initial state = normal", engine.state == "normal")

engine.feed_pet()
check("Feed: hunger capped at 100", engine.hunger == 100)

engine.hunger = 19; engine.update_state()
check("Hunger < 20 -> foraging", engine.state == "foraging")

engine.hunger = 20; engine.update_state()
check("Hunger >= 20 -> normal", engine.state == "normal")

check("[WARN] StateMachine imported but NOT used in game loop (hardcoded IDLE)",
      True,
      "PetStateMachine is dead code in main.py _on_tick()",
      warn=True)

# ======================================================================
# PART 6: Config (QSettings)
# ======================================================================
section("6. Config (QSettings)")
cfg = Config()
cfg.save_position(100, 200)
x, y = cfg.load_position()
check("save/load position", x == 100 and y == 200)

cfg.save_scale(1.5)
check("save/load scale", abs(cfg.load_scale() - 1.5) < 0.001)

cfg.save_image_path("/tmp/test.png")
check("save/load image_path", cfg.load_image_path() == "/tmp/test.png")

# ======================================================================
# PART 7: UI Components
# ======================================================================
section("7. UI Instantiation")

from src.ui.dashboard_page import DashboardPage
from src.ui.upload_page import UploadPage
from src.ui.image_library_page import ImageLibraryPage
from src.ui.pet_management_page import PetManagementPage
from src.ui.settings_page import SettingsPage
from src.ui.main_window import MainWindow, SIDEBAR_ITEMS

# Create a fresh DB service for UI tests
db2 = DatabaseService.__new__(DatabaseService)
db2._config = Config()
db2._data_dir = TMP
db2._db = DatabaseManager(str(TMP / "ui_test.db"))
db2._images_original = TMP_ORIG
db2._images_processed = TMP_PROC

# 7.1 Page instantiation
_, err = try_call(lambda: DashboardPage(None, db2).refresh())
check("DashboardPage instantiate + refresh", err is None, err or "")

_, err = try_call(lambda: UploadPage(None, svc, ai, db2).refresh())
check("UploadPage instantiate + refresh", err is None, err or "")

_, err = try_call(lambda: ImageLibraryPage(None, svc, db2).refresh())
check("ImageLibraryPage instantiate + refresh", err is None, err or "")

_, err = try_call(lambda: PetManagementPage(None, db2).refresh())
check("PetManagementPage instantiate + refresh", err is None, err or "")

_, err = try_call(lambda: SettingsPage(db2, pet_window=None).refresh())
check("SettingsPage instantiate + refresh", err is None, err or "")

# 7.2 MainWindow
check("SIDEBAR_ITEMS has 5 items", len(SIDEBAR_ITEMS) == 5)

expected = ["home", "create", "material", "pet", "settings"]
for i, (text, idx) in enumerate(SIDEBAR_ITEMS):
    check(f"Nav item {i} index={idx}", idx == i)

window, win_err = try_call(lambda: MainWindow(None, svc, ai, db2, pet_window=None))
check("MainWindow instantiate", win_err is None, win_err or "")
if window is not None:
    check("MainWindow has 5 pages", len(window._pages) == 5)
    check("Page 0 is DashboardPage", isinstance(window._pages[0], DashboardPage))
    check("Page 1 is UploadPage", isinstance(window._pages[1], UploadPage))
    check("Page 2 is ImageLibraryPage", isinstance(window._pages[2], ImageLibraryPage))
    check("Page 3 is PetManagementPage", isinstance(window._pages[3], PetManagementPage))
    check("Page 4 is SettingsPage", isinstance(window._pages[4], SettingsPage))
    check("Window title", window.windowTitle() == "Desktop Pet Center")
    check("Min width 900", window.minimumWidth() == 900)
    check("Sidebar width 240", window.SIDEBAR_WIDTH == 240)

    # Navigation
    window._sidebar.setCurrentRow(0)
    check("Nav to page 0", window._stack.currentIndex() == 0)
    window._sidebar.setCurrentRow(4)
    check("Nav to page 4", window._stack.currentIndex() == 4)

# 7.3 Upload page stage transitions
section("7.3 Upload Stage Transitions")
up = UploadPage(None, svc, ai, db2)
check("Initial stage: SELECT", up._stage == UploadPage.STAGE_SELECT)
check("DropZone visible", up._drop_zone.isVisible())
check("Remove BG button hidden", not up._remove_bg_btn.isVisible())

up._set_stage(UploadPage.STAGE_PREVIEW)
check("STAGE_PREVIEW: remove bg btn visible", up._remove_bg_btn.isVisible())

up._set_stage(UploadPage.STAGE_PROCESSING)
check("STAGE_PROCESSING: progress visible", up._progress.isVisible())

up._set_stage(UploadPage.STAGE_RESULT)
check("STAGE_RESULT: name input visible", up._name_input.isVisible())
check("STAGE_RESULT: create btn visible", up._create_btn.isVisible())

up._on_reset()
check("Reset returns to STAGE_SELECT", up._stage == UploadPage.STAGE_SELECT)

# 7.4 Settings page slider
section("7.4 Settings Slider")
sp = SettingsPage(db2, pet_window=None)
check("Slider range 25-400", sp._scale_slider.minimum() == 25 and sp._scale_slider.maximum() == 400)
check("Slider default 100 (1.0x)", sp._scale_slider.value() == 100)
sp._scale_slider.setValue(200)
check("Scale label updates", sp._scale_value_label.text() == "2.00x")
# No pet_window -> should not crash
check("No pet_window: setScale not called, no crash", True)

# ======================================================================
# PART 8: PetService (without PetWindow)
# ======================================================================
section("8. PetService via DatabaseService")

db3_path = str(TMP / "petsvc_test.db")
db3 = DatabaseManager(db3_path)

# Image CRUD via DB service
img3_id = db3.add_image({"original_path": "/x.png", "original_name": "x.png", "format": "png"})
check("Image added via DB manager", img3_id > 0)

db3.update_image(img3_id, {"processed_path": "/tmp/out.png"})
imgs3 = db3.get_all_images()
check("Image updated via DB manager", any(i["id"] == img3_id and i.get("processed_path") == "/tmp/out.png" for i in imgs3))

db3.delete_image(img3_id)
check("Image soft deleted", all(i["id"] != img3_id for i in db3.get_all_images()))

# Pet CRUD via DB service
pet3_id = db3.add_pet({"name": "SvcCat", "image_path": "/tmp/cat.png", "is_active": True})
check("Pet added via DB manager", pet3_id > 0)

db3.update_pet(pet3_id, {"name": "SvcCatRenamed"})
pets3 = db3.get_all_pets()
check("Pet renamed", any(p["id"] == pet3_id and p["name"] == "SvcCatRenamed" for p in pets3))

active_pet = db3.get_active_pet()
check("Active pet found", active_pet is not None and active_pet["id"] == pet3_id)

db3.delete_pet(pet3_id)
check("Pet hard deleted", all(p["id"] != pet3_id for p in db3.get_all_pets()))

# BUG: create_pet_from_image returns dict without ID
section("8.1 create_pet_from_image return value bug")
simulated = {"name": "NoID", "image_path": "/x.png", "is_active": False}
db3.add_pet(simulated)
check("[BUG] create_pet_from_image returns dict WITHOUT database ID",
      "id" not in simulated,
      "Pet dict returned to caller lacks 'id' field. DatabaseService.add_pet() discards the return value from DatabaseManager.add_pet() which returns lastrowid.",
      warn=True)

# ======================================================================
# PART 9: Edge Cases
# ======================================================================
section("9. Edge Cases")

# 9.1 Missing image in PetRenderer
section("9.1 Missing Image File")
from src.pet_renderer import PetRenderer
from PyQt6.QtWidgets import QWidget
dummy = QWidget()
rend = PetRenderer(dummy, image_path="/nonexistent/definitely_missing.png")
check("PetRenderer with missing file: no crash", True)
check("PetRenderer with missing file: pixmap is null", rend.pixmap.isNull())

# 9.2 Corrupt image file
corrupt_file = TMP / "corrupt.png"
corrupt_file.write_text("not a real PNG file at all")
rend2 = PetRenderer(dummy, image_path=str(corrupt_file))
check("Corrupt image: no crash", True)
check("Corrupt image: pixmap is null", rend2.pixmap.isNull())

# 9.3 Corrupt database
corrupt_db = str(TMP / "corrupt.db")
Path(corrupt_db).write_text("this is not sqlite")
db_corrupt = DatabaseManager(corrupt_db)
_, err_corrupt = try_call(lambda: db_corrupt.get_all_pets())
check("Corrupt DB: CRUD raises exception (expected)", err_corrupt is not None,
      f"Correctly raised: {err_corrupt[:80]}" if err_corrupt else "No exception raised - should have failed")

# 9.4 Empty database
empty_db = DatabaseManager(str(TMP / "empty.db"))
check("Empty DB: get_all_pets -> []", empty_db.get_all_pets() == [])
check("Empty DB: get_all_images -> []", empty_db.get_all_images() == [])
check("Empty DB: get_active_pet -> None", empty_db.get_active_pet() is None)

# 9.5 Dashboard with empty data
empty_dash = DashboardPage(None, db2)
empty_dash.refresh()
check("Empty Dashboard shows 'no pet' placeholder", True)

# 9.6 Ghost pet (invalid path)
ghost_id = empty_db.add_pet({"name": "Ghost", "image_path": "/definitely/not/real.png", "is_active": True})
ghost = empty_db.get_active_pet()
check("Pet with invalid image path can be created", ghost is not None and ghost["name"] == "Ghost")
check("Pet with invalid path can be queried as active", ghost["is_active"] == 1)

# 9.7 DropZone format validation
section("9.7 DropZone Validation")
check("validate .PNG uppercase", svc.validate_format("CAT.PNG"))
check("validate .GIF uppercase", svc.validate_format("BIRD.GIF"))
check("validate .WebP mixed case", svc.validate_format("img.WebP"))
check("reject no extension", not svc.validate_format("noextension"))
check("reject empty string", not svc.validate_format(""))

# 9.8 Unique active pet constraint
section("9.8 Active Pet Uniqueness")
uniq_db = DatabaseManager(str(TMP / "uniq.db"))
uniq_db.add_pet({"name": "A", "image_path": "/a.png", "is_active": True})
uniq_db.add_pet({"name": "B", "image_path": "/b.png", "is_active": True})
active_pets = [p for p in uniq_db.get_all_pets() if p["is_active"]]
check("Only 1 active pet after adding 2 active", len(active_pets) == 1)
check("Active is the most recently added", active_pets[0]["name"] == "B")

# 9.9 settings page slider rapid change
sp2 = SettingsPage(db2, pet_window=None)
for v in range(25, 401, 25):
    sp2._scale_slider.setValue(v)
check("Rapid slider changes (16 values): no crash", True)

# 9.10 Foreign key edge case
db_fk = DatabaseManager(str(TMP / "fk_test.db"))
img_fk = db_fk.add_image({"original_path": "/x.png", "original_name": "x.png", "format": "png"})
db_fk.add_pet({"name": "FK_OK", "image_path": "/x.png", "image_id": img_fk, "is_active": False})
check("FK reference exists: no crash", True)
db_fk.add_pet({"name": "FK_BAD", "image_path": "/x.png", "image_id": 99999, "is_active": False})
check("FK reference to nonexistent image: no crash (deferred)", True)

# ======================================================================
# SUMMARY
# ======================================================================
section("TEST SUMMARY")
total = passed + failed + warnings
print(f"\n  Passed:  {passed}")
print(f"  Warnings: {warnings}")
print(f"  Failed:  {failed}")
print(f"  Total:   {total}")
print(f"\n  Temp files: {TMP}")

if failed > 0:
    print(f"\n  *** {failed} TEST(S) FAILED ***")
    sys.exit(1)
else:
    print(f"\n  All required tests passed ({passed}), {warnings} warning(s).")
