"""Kivy GUI front-end for the Stanza-based text anonymizer.

Run this module to open a simple GUI that allows:
- paste or load English text
- anonymize named entities using Stanza
- save anonymized output to a file
"""
import threading
import tkinter as tk
from tkinter import filedialog

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

import anonymizer

KV = """
<RootWidget>:
    orientation: "vertical"
    padding: 8
    spacing: 8

    Label:
        text: "Input text (English)"
        size_hint_y: None
        height: 24

    TextInput:
        id: input_text
        text: root.input_text
        on_text: root.input_text = self.text
        multiline: True
        size_hint_y: 0.45

    BoxLayout:
        size_hint_y: None
        height: 40
        spacing: 8

        Button:
            text: "Load from file..."
            on_release: root.load_file()
        Button:
            id: anonymize_btn
            text: "Anonymize"
            disabled: not root.pipeline_loaded
            on_release: root.anonymize_text()
        Button:
            text: "Save result..."
            on_release: root.save_file()

    Label:
        id: status_label
        text: root.status_text
        size_hint_y: None
        height: 20

    Label:
        text: root.model_info_text
        size_hint_y: None
        height: 20

    Label:
        text: "Anonymized output"
        size_hint_y: None
        height: 24

    TextInput:
        id: output_text
        text: root.output_text
        multiline: True
        size_hint_y: 0.45
        readonly: True
"""


class RootWidget(BoxLayout):
    input_text = StringProperty("")
    output_text = StringProperty("")
    status_text = StringProperty("Ready. Stanza model will be loaded on first run.")
    model_info_text = StringProperty("Models: not checked")
    pipeline_loaded = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pipeline_loading = False

    def _load_pipeline_background(self):
        """Load the Stanza pipeline in a background thread to avoid blocking UI."""
        self.status_text = "Checking / loading Stanza models..."
        self.model_info_text = "Models: downloading or locating models..."
        try:
            anonymizer._ensure_pipeline()  # type: ignore[attr-defined]
            self.pipeline_loaded = True
            self._pipeline_loading = False
            self.status_text = "Stanza loaded. Ready."
            self.model_info_text = "Models: available"
        except Exception as exc:
            self.status_text = f"Failed to load Stanza: {exc}"
            self.model_info_text = "Models: not available"

    def ensure_pipeline(self):
        """Ensure the pipeline is loaded; spawn a thread if not."""
        if not self._pipeline_loading and not self.pipeline_loaded:
            self._pipeline_loading = True
            thread = threading.Thread(target=self._load_pipeline_background, daemon=True)
            thread.start()

    def load_file(self) -> None:
        """Open a file dialog and load file content into the input box."""
        # Use tkinter filedialog (no tkinter mainloop required)
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.askopenfilename(title="Open text file", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        root.destroy()
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as fh:
                    self.input_text = fh.read()
                self.status_text = f"Loaded: {filename}"
            except Exception as exc:
                self.status_text = f"Failed to load file: {exc}"

    def save_file(self) -> None:
        """Open a file dialog and save anonymized output to a file."""
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.asksaveasfilename(
            title="Save anonymized text",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        root.destroy()
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as fh:
                    fh.write(self.output_text)
                self.status_text = f"Saved: {filename}"
            except Exception as exc:
                self.status_text = f"Failed to save file: {exc}"

    def anonymize_text(self) -> None:
        """Run anonymization on the input text (may load models first)."""
        text = self.input_text
        if not text.strip():
            self.status_text = "Input is empty."
            return

        # Ensure pipeline is (or will be) loaded
        self.ensure_pipeline()

        def _worker():
            try:
                # Run anonymization (may be slow). Schedule UI updates on the main thread.
                Clock.schedule_once(lambda dt: setattr(self, "status_text", "Anonymizing..."))
                result = anonymizer.anonymize_with_stanza(text)
                Clock.schedule_once(lambda dt, res=result: setattr(self, "output_text", res))
                Clock.schedule_once(lambda dt: setattr(self, "status_text", "Anonymization complete."))
            except Exception as exc:
                Clock.schedule_once(lambda dt, e=exc: setattr(self, "status_text", f"Error during anonymization: {e}"))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()


class AnonymizerApp(App):
    def build(self):
        Builder.load_string(KV)
        root = RootWidget()
        return root

    def on_start(self):
        """Start loading the Stanza pipeline in background when app starts."""
        try:
            if getattr(self, "root", None) is not None:
                self.root.ensure_pipeline()
        except Exception:
            # Do not crash the app if background startup fails; status_text will show errors.
            pass


if __name__ == "__main__":
    AnonymizerApp(title="Text Anonymizer (Stanza + Kivy)").run()
