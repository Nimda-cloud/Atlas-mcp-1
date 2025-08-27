# Wrapper referencing original (to be relocated fully later)
import runpy, pathlib
runpy.run_path(str((pathlib.Path(__file__).resolve().parent.parent / 'mock_ollama_server.py')))