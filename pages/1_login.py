import sys, importlib.util
from pathlib import Path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("page_login", root / "app" / "pages" / "1_login.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
