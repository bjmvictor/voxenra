"""Collect dynamically discovered decoder entry points and their native wheels."""
from PyInstaller.utils.hooks import collect_all, copy_metadata

hiddenimports, binaries, datas = [], [], []
for package in ("pylibjpeg", "openjpeg", "jpeg_ls", "_gdcm"):
    package_data, package_binaries, package_imports = collect_all(package)
    datas += package_data
    binaries += package_binaries
    hiddenimports += package_imports
# Native extensions are top-level modules in the codec wheels.
hiddenimports += ["_openjpeg", "_CharLS", "gdcm"]
for distribution in ("pylibjpeg", "python-gdcm", "pylibjpeg-openjpeg", "pyjpegls"):
    datas += copy_metadata(distribution)
