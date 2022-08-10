from pathlib import Path
import os
import sys

path = str(Path(os.path.abspath(__file__)).parent.parent)
sys.path.insert(1, path)
