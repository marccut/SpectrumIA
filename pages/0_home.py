import sys, importlib.util
from pathlib import Path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("page_home", root / "app" / "pages" / "0_home.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
