# hook-WC_Vars_PSIV.py
from PyInstaller.utils.hooks import collect_submodules

# Collect all submodules to ensure they're included
hiddenimports = collect_submodules('src')