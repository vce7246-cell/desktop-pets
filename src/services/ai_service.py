"""AI service: unified entry point for AI-powered image processing.

Currently supports background removal via rembg (u2net ONNX model).
The service is designed for extension — new capabilities (generation,
style transfer, etc.) are added as new methods, each returning a
QThread that emits ``finished(str)`` / ``error(str)`` signals.
"""
from src.image_processor import BackgroundRemover


class AIService:
    """Stateless factory for AI-processing background threads.

    Each method returns a *stopped* QThread subclass instance.
    Call ``.start()`` on the returned object to begin processing,
    and connect to its ``finished`` / ``error`` signals for results.
    """

    def remove_background(
        self,
        input_path: str,
        output_path: str,
        parent=None,
    ) -> BackgroundRemover:
        """Create a background-removal thread (rembg).

        Args:
            input_path:  Source image file path.
            output_path: Where to write the result PNG.
            parent:      Optional QObject parent for thread lifetime.

        Returns:
            BackgroundRemover (QThread subclass). The caller must:
            1. Connect to ``finished`` (str) and ``error`` (str) signals.
            2. Call ``.start()`` to begin processing.
        """
        return BackgroundRemover(input_path, output_path, parent)
