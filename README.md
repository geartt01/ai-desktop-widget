# AI Desktop Widget

A tiny always-on-top desktop assistant that talks to a **local AI model through [Ollama](https://ollama.com)**.
It sits in the corner of the screen as a small 🤖 button. Click it, ask a question, get a short answer, and
nothing leaves your computer.

I built it for myself and my family: it's used day to day for quick questions while working on PowerPoint and Excel.

**Stack:** Python · Tkinter / CustomTkinter · Ollama REST API (Gemma, Mistral) · PyInstaller

## Features

- Borderless, always-on-top widget that collapses to a 50×50 button
- Runs fully offline against a local model (`gemma` by default, any Ollama model works)
- Requests run on a background thread, so the UI never freezes while the model thinks
- Clear error message when Ollama isn't running
- Keyboard shortcuts while focused: **Ctrl+Shift+V** open, **Ctrl+Shift+C** minimize, **Enter** / **Ctrl+Shift+A** ask
- Packaged into a single Windows `.exe` with PyInstaller (`ai_widget.spec`, custom icon)

## Run it

1. Install [Ollama](https://ollama.com/download) and pull a model:
   ```bash
   ollama pull gemma
   ```
2. Install the Python dependencies (Python 3.10+):
   ```bash
   pip install -r requirements.txt
   ```
3. Start the widget:
   ```bash
   python ai_widget.py
   ```

To use another model, change `MODEL` at the top of `ai_widget.py` (for example `"mistral"`).

## Build the .exe (Windows)

```bash
pip install pyinstaller
pyinstaller ai_widget.spec
```

The executable is written to `dist/ai_widget.exe`.

## How it works

`ask_ollama()` sends the prompt to Ollama's `/api/generate` endpoint on a worker thread. Tkinter isn't
thread-safe, so the answer is put on a queue and the main thread picks it up every 100 ms and updates the chat box.
