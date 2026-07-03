"""Image background removal using rembg (u2net ONNX model).

Runs in a QThread to keep the UI responsive during processing (~2-10s CPU).
"""
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal


def make_output_path(input_path: str) -> str:
    """Generate a non-colliding output path: ``{stem}_nobg.png`` in the same directory.

    If the file already exists, append ``_2``, ``_3``, etc. before ``.png``.
    """
    source = Path(input_path)
    parent = source.parent
    stem = source.stem

    candidate = parent / f"{stem}_nobg.png"
    if not candidate.exists():
        return str(candidate)

    n = 2
    while True:
        candidate = parent / f"{stem}_nobg_{n}.png"
        if not candidate.exists():
            return str(candidate)
        n += 1


class BackgroundRemover(QThread):
    """Runs rembg.remove() in a background thread.

    Signals (all delivered in the main thread via Qt queued connections):

        finished (str)  — output file path on success
        error    (str)  — human-readable error message on failure
    """

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self, input_path: str, output_path: str, parent=None,
    ) -> None:
        super().__init__(parent)
        self._input = input_path
        self._output = output_path

    def run(self) -> None:
        """Entry point for QThread. Called via .start()."""
        try:
            # Lazy import — allows the app to start even if rembg is missing
            from rembg import remove
        except ImportError:
            self.error.emit(
                "未安装 rembg 库。请在终端运行: pip install rembg"
            )
            return

        try:
            with open(self._input, "rb") as fh:
                input_bytes = fh.read()

            output_bytes = remove(input_bytes)

            with open(self._output, "wb") as fh:
                fh.write(output_bytes)

            self.finished.emit(self._output)

        except FileNotFoundError:
            self.error.emit("当前图片文件不存在，请先更换宠物图片。")
        except PermissionError:
            self.error.emit(f"无法保存处理结果: {self._output}（权限不足）")
        except Exception as exc:
            # rembg model download failures, corrupt images, etc.
            msg = str(exc)
            if not msg.strip():
                msg = type(exc).__name__
            self.error.emit(f"图片处理失败: {msg}")
