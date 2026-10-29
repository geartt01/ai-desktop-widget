"""AI Widget: a small always-on-top desktop assistant powered by a local Ollama model.

The widget sits in the top-left corner as a 50x50 button. Click it (or press Ctrl+Shift+V)
to open the chat panel, type a question and press Enter. Answers come from a model running
locally through Ollama, so nothing leaves your computer.
"""

import queue
import threading
import tkinter as tk

import customtkinter as ctk
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma"  # any model you have pulled with `ollama pull <name>`, e.g. "mistral"
TIMEOUT_SECONDS = 120

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


def ask_ollama(prompt, callback):
    """Send the prompt to Ollama on a background thread and pass the answer to callback."""

    def fetch():
        try:
            res = requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "prompt": prompt, "stream": False},
                timeout=TIMEOUT_SECONDS,
            )
            res.raise_for_status()
            answer = res.json().get("response", "Error: No response")
        except requests.exceptions.ConnectionError:
            answer = "Error: can't reach Ollama. Is it running? (ollama serve)"
        except Exception as e:
            answer = f"Error: {e}"
        callback(answer)

    threading.Thread(target=fetch, daemon=True).start()


class AIWidget:
    def __init__(self, root):
        self.root = root
        self.mini = True

        # Window setup: borderless, always on top, starts minimized
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.geometry("50x50+20+20")
        root.configure(bg="#1f1f1f")

        # Mini view button
        self.mini_btn = ctk.CTkButton(
            root,
            text="🤖",
            font=("Segoe UI", 16),
            command=self.expand,
            fg_color="#2e2e2e",
            hover_color="#444",
        )
        self.mini_btn.pack(expand=True, fill="both")

        # Full chat frame
        self.chat_frame = ctk.CTkFrame(root, fg_color="#1f1f1f")

        self.header_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=5, pady=(5, 0))

        self.title_label = ctk.CTkLabel(self.header_frame, text="AI Widget", font=("Segoe UI", 14, "bold"))
        self.title_label.pack(side="left", padx=5)

        self.close_btn = ctk.CTkButton(
            self.header_frame, text="–", width=30, command=self.minimize,
            fg_color="transparent", hover_color="#333",
        )
        self.close_btn.pack(side="right", padx=2)

        self.exit_btn = ctk.CTkButton(
            self.header_frame, text="✖", width=30, command=self.close_widget,
            fg_color="transparent", hover_color="#ff5555", text_color="#ff5555",
        )
        self.exit_btn.pack(side="right", padx=2)

        self.text = ctk.CTkTextbox(self.chat_frame, height=180, font=("Segoe UI", 11), wrap="word")
        self.text.pack(padx=10, pady=(5, 0), fill="both", expand=True)
        self.text.configure(state="disabled")

        self.entry = ctk.CTkEntry(self.chat_frame, placeholder_text="Ask me anything...", font=("Segoe UI", 12))
        self.entry.pack(padx=10, pady=5, fill="x")
        self.entry.bind("<Return>", lambda event: self.ask())

        self.ask_btn = ctk.CTkButton(
            self.chat_frame, text="Ask", command=self.ask, font=("Segoe UI", 12), corner_radius=10,
        )
        self.ask_btn.pack(padx=10, pady=(0, 10), fill="x")

        self.responses = queue.Queue()
        root.after(100, self.bind_keys)
        root.after(100, self.poll_responses)

    def bind_keys(self):
        """Keyboard shortcuts (work while the widget has focus)."""
        self.root.bind("<Control-Shift-V>", lambda event: self.expand())  # open
        self.root.bind("<Control-Shift-C>", lambda event: self.minimize())  # minimize
        self.root.bind("<Control-Shift-A>", lambda event: self.ask())  # ask

    def expand(self):
        self.mini = False
        self.root.geometry("360x320+20+20")
        self.mini_btn.pack_forget()
        self.chat_frame.pack(fill="both", expand=True)
        self.entry.focus_set()

    def minimize(self):
        self.mini = True
        self.chat_frame.pack_forget()
        self.root.geometry("50x50+20+20")
        self.mini_btn.pack(expand=True, fill="both")

    def close_widget(self):
        self.root.destroy()

    def show_text(self, message):
        self.text.configure(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, message)
        self.text.configure(state="disabled")

    def ask(self):
        prompt = self.entry.get()
        if not prompt.strip():
            return
        self.entry.delete(0, tk.END)
        self.show_text("Thinking...")
        self.ask_btn.configure(state="disabled")
        ask_ollama(prompt, self.display_response)

    def display_response(self, response):
        # Called from the worker thread. Tkinter isn't thread-safe, so the answer goes
        # into a queue and the main thread picks it up in poll_responses().
        self.responses.put(response)

    def poll_responses(self):
        try:
            while True:
                response = self.responses.get_nowait()
                self.show_text(response.strip())
                self.ask_btn.configure(state="normal")
        except queue.Empty:
            pass
        self.root.after(100, self.poll_responses)


if __name__ == "__main__":
    root = tk.Tk()
    app = AIWidget(root)
    root.mainloop()
