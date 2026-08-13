"""Render every Manim scene from animations.ipynb, in notebook order, as one video."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from manim import *
from manim import tempconfig

HERE = Path(__file__).resolve().parent
NOTEBOOK = HERE / "animations.ipynb"
OUT_DIR = HERE / "videos_finales"
FINAL_VIDEO = OUT_DIR / "tramo1.mp4"


def scene_classes_from_notebook(path: Path) -> list[type[Scene]]:
    nb = json.loads(path.read_text())
    namespace: dict = {"__name__": "tramo1_scenes"}
    exec("from manim import *\nimport numpy as np", namespace)

    scenes: list[type[Scene]] = []
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if "(Scene)" not in src:
            continue
        body = "\n".join(
            line for line in src.splitlines() if not line.startswith("%%")
        )
        before = set(namespace)
        exec(body, namespace)
        for name in namespace.keys() - before:
            obj = namespace[name]
            if isinstance(obj, type) and issubclass(obj, Scene) and obj is not Scene:
                scenes.append(obj)
    return scenes


SCENE_CLASSES = scene_classes_from_notebook(NOTEBOOK)


class Tramo1Animation(Scene):
    def construct(self):
        if not SCENE_CLASSES:
            raise RuntimeError(f"No Scene classes found in {NOTEBOOK}")

        for i, scene_cls in enumerate(SCENE_CLASSES):
            scene_cls.construct(self)
            leftover = list(self.mobjects)
            if leftover:
                self.play(*[FadeOut(mob) for mob in leftover], run_time=0.6)
            self.clear()
            if i < len(SCENE_CLASSES) - 1:
                self.wait(0.1)

    def render(self, *args, **kwargs):
        super().render(*args, **kwargs)
        src = Path(self.renderer.file_writer.movie_file_path)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, FINAL_VIDEO)
        print(f"Saved {FINAL_VIDEO}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempconfig(
        {
            "quality": "medium_quality",
            "preview": False,
            "verbosity": "WARNING",
            "media_dir": str(OUT_DIR / "_manim"),
            "output_file": "tramo1",
        }
    ):
        Tramo1Animation().render()


if __name__ == "__main__":
    main()
