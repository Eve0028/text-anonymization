# Text Anonymizer (Stanza + Kivy)

This project is a simple desktop tool to anonymize English text using Stanza's NER
models, with a small Kivy GUI for loading, processing, and saving text.

## Features
- Replace named entity spans with bracketed labels (e.g. `[PERSON]`, `[LOCATION]`).
- Simple GUI to paste text, load from file, anonymize, and save results.
- Uses Stanza for robust NER and falls back to token-based BIO parsing if needed.

## Requirements
- Python 3.9+ recommended
- See `requirements.txt`.

## Quick start (development)

1. Create and activate a virtual environment:

```bash
python -m venv venv
# Windows
venv\\Scripts\\activate
# macOS / Linux
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the GUI:

```bash
python main.py
```

On first run, Stanza may download English models (this can take a minute).

## Building a Windows executable

Using PyInstaller. Example command:

```bash
pyinstaller --onefile --windowed --log-level=INFO main.py
```

Notes:
- You may need to include the `stanza` models folder in the distribution or ensure
  the target system can download the models on first run.
- Kivy packaging on Windows may require additional steps depending on system
  configuration; consult the official Kivy packaging docs if issues arise.
 
Bundling models with the executable (recommended)

1. Download models into the repository:

```bash
python download_models.py
```

2. Build with PyInstaller and include the `stanza_models` folder:

```bash
pyinstaller --onefile --windowed --add-data "stanza_models;stanza_models" --log-level=INFO main.py
```

Alternatively run the provided script on Windows:

```powershell
.\build_exe.bat
```

## Files
- `main.py` — Kivy GUI front-end
- `anonymizer.py` — Stanza-based anonymization logic
- `requirements.txt` — Python dependencies

## License
MIT
