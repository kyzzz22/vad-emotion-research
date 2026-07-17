from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "visualization" / "dreamer-vad-3d"
OUTPUT = ROOT / "visualization" / "VAD3D_macOS_演示包.zip"
PACKAGE_ROOT = "VAD3D_Demo"

FILES = [
    "index.html",
    "styles.css",
    "app.js",
    "start_demo.command",
    "start_demo.bat",
    "start_demo.ps1",
    "演示说明.txt",
    "vendor/three.core.js",
    "vendor/three.module.js",
    "vendor/OrbitControls.js",
]


with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
    for relative_name in FILES:
        source_path = SOURCE / relative_name
        archive_name = f"{PACKAGE_ROOT}/{relative_name}"
        info = ZipInfo.from_file(source_path, archive_name)
        info.create_system = 3
        mode = 0o755 if relative_name.endswith(".command") else 0o644
        info.external_attr = (mode | 0o100000) << 16
        info.compress_type = ZIP_DEFLATED
        with source_path.open("rb") as source_file:
            archive.writestr(info, source_file.read(), compress_type=ZIP_DEFLATED, compresslevel=9)

print("macOS demo package generated")
