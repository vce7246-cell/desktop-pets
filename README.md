<p align="center">
  <img src="src/assets/default_pet.png" width="128" alt="Desktop Pet">
</p>

<h1 align="center">🦊 Desktop Pet</h1>

<p align="center">一个轻量级、跨平台的桌面伴侣应用。上传任意图片或 GIF 作为你的桌宠——它悬浮在所有窗口之上，跟随鼠标光标运动，并根据光标速度和距离做出不同的动画反应。</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt-6.x-green.svg" alt="PyQt6">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License">
</p>

---

## ✨ 特性

- 🪟 **无边框透明窗口** — 桌宠悬浮于桌面之上，无边框、无背景、无任务栏图标
- 🖱️ **鼠标跟随** — 基于物理的弹性跟随算法，宠物自然地跟在光标周围
- 🎭 **5 种动画状态** — IDLE（呼吸）、FOLLOWING（跟随）、RUNNING（倾斜）、EXCITED（弹跳）、DRAGGED（挤压）
- 🖼️ **自定义图片/GIF** — 拖放或选择任意 PNG/JPG/GIF/WebP 作为宠物
- 🤖 **AI 一键抠图** — 内置 rembg 模型，自动去除图片背景
- 🎛️ **Desktop Pet Center** — Steam/Wallpaper Engine 风格的暗色主题管理界面
- 📦 **单文件打包** — PyInstaller 打包为单个 exe，无需安装 Python
- 💾 **数据持久化** — SQLite 存储素材库、桌宠记录，支持软删除和自动恢复

## 🎬 快速开始

### 环境要求

- Python 3.11+
- Windows 10+ 或 macOS

### 安装运行

```bash
# 克隆仓库
git clone https://github.com/vce7246-cell/desktop-pets.git
cd desktop-pets

# 创建虚拟环境
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# 或 venv\Scripts\activate    # Windows CMD

# 安装依赖
pip install -r requirements.txt

# 运行
python src/main.py
```

### 打包为 exe

```bash
pyinstaller DesktopPet.spec
# 输出: dist/DesktopPet.exe
```

## 🎮 使用方式

| 操作 | 方式 |
|------|------|
| 更换宠物 | 右键托盘图标 → 更换宠物 |
| 去除背景 | 右键托盘图标 → 去除背景（AI 自动抠图） |
| 管理中心 | 右键托盘图标 → 管理中心（素材库/桌宠管理/设置） |
| 拖拽桌宠 | 鼠标左键按住宠物拖动 |
| 缩放大小 | 管理中心 → 设置 → 滑块调节 (0.25×–4.0×) |
| 退出程序 | 右键托盘图标 → 退出 |

## 🏗️ 项目结构

```
desktop-pets/
├── src/
│   ├── main.py                  # 入口：QApplication、托盘图标、游戏循环
│   ├── pet_window.py            # PetWindow：透明浮窗、鼠标跟随
│   ├── pet_renderer.py          # 图片/GIF 渲染（QLabel + QMovie）
│   ├── state_machine.py         # 5 状态机（IDLE/FOLLOWING/RUNNING/EXCITED/DRAGGED）
│   ├── pet_status.py            # 宠物状态引擎（饥饿值/喂食）
│   ├── mouse_tracker.py         # 全局光标追踪（60Hz QTimer）
│   ├── config.py                # QSettings 配置读写
│   ├── image_processor.py       # rembg 后台抠图线程
│   ├── database/
│   │   └── db_manager.py        # SQLite 数据库管理（含自动恢复）
│   ├── services/
│   │   ├── database_service.py  # 数据库服务层
│   │   ├── image_service.py     # 图片验证/导入/路径生成
│   │   ├── ai_service.py        # AI 抠图服务
│   │   └── pet_service.py       # 桌宠生命周期管理
│   ├── ui/
│   │   ├── main_window.py       # Desktop Pet Center 主窗口
│   │   ├── dashboard_page.py    # 首页仪表盘
│   │   ├── upload_page.py       # 创建桌宠（上传+抠图流程）
│   │   ├── image_library_page.py# 我的素材库
│   │   ├── pet_management_page.py# 我的桌宠管理
│   │   └── settings_page.py     # 设置页面
│   └── assets/
│       └── default_pet.png      # 默认宠物图片
├── tests/
│   └── qa_test_suite.py         # QA 自动化测试（111 项）
├── DesktopPet.spec              # PyInstaller 打包配置
├── requirements.txt
└── README.md
```

## 🎨 Desktop Pet Center

<p align="center"><em>暗色现代主题，左侧导航栏，卡片式布局</em></p>

| 页面 | 功能 |
|------|------|
| 🏠 首页 | 统计概览：桌宠数量、素材数量、当前状态 |
| ✨ 创建桌宠 | 拖拽上传 → 预览 → AI 抠图 → 命名创建 |
| 🖼️ 我的素材 | 卡片网格展示所有素材，右键菜单操作 |
| 🐾 我的桌宠 | 管理已创建的桌宠，一键切换 |
| ⚙️ 设置 | 宠物缩放滑块、关于信息 |

## 🧪 测试

```bash
# 需要从纯 ASCII 路径运行（Windows 上 PyQt6 的已知限制）
cp tests/qa_test_suite.py /tmp/
cd /tmp
python qa_test_suite.py
```

覆盖：模块导入、数据库 CRUD、图片服务、AI 服务、状态机、UI 组件、异常恢复。

## 📄 技术栈

| 层 | 技术 |
|----|------|
| 语言 | Python 3.11+ |
| GUI 框架 | PyQt6 |
| AI 抠图 | rembg + onnxruntime |
| 数据库 | SQLite (WAL 模式) |
| 打包 | PyInstaller |

详见 [.tech-stack.md](.tech-stack.md) 和 [.game-design-document.md](.game-design-document.md)。

## 📝 License

MIT
