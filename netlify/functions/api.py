import sys
from pathlib import Path
from mangum import Mangum

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from main import app

handler = Mangum(app)
