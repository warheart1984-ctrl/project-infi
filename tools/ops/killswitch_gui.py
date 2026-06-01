"""Optional desktop kill-switch panel for the AAIS lineage tools.

This window is intentionally simple: it stays on top and exposes the same
pause, stop, kill, and resume controls as the CLI helpers.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox

from emergency_stop import StopLevel, get_kill_switch
from killswitch_init import init_kill_switch


BG_COLOR = "#0a0a0a"
PANEL_COLOR = "#111111"
TEXT_MUTED = "#555555"
TEXT_STATUS_OK = "#44ff88"
TEXT_STATUS_WARN = "#ffaa00"
TEXT_STATUS_STOP = "#ff4444"
TEXT_STATUS_KILL = "#880000"


class KillSwitchPanel(tk.Tk):
    """Simple always-on-top operator panel for emergency control."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Emergency Control")
        self.geometry("420x320")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(bg=BG_COLOR)

        self.ks = get_kill_switch()
        init_kill_switch()

        self._build_ui()
        self._poll_state()

    def _build_ui(self) -> None:
        tk.Label(
            self,
            text="EMERGENCY CONTROL",
            font=("Courier New", 14, "bold"),
            fg=TEXT_STATUS_STOP,
            bg=BG_COLOR,
        ).pack(pady=(20, 5))

        tk.Label(
            self,
            text="Operator kill switch panel",
            font=("Courier New", 9),
            fg=TEXT_MUTED,
            bg=BG_COLOR,
        ).pack(pady=(0, 15))

        self.status_label = tk.Label(
            self,
            text="RUNNING",
            font=("Courier New", 11, "bold"),
            fg=TEXT_STATUS_OK,
            bg=BG_COLOR,
        )
        self.status_label.pack(pady=(0, 20))

        button_frame = tk.Frame(self, bg=BG_COLOR)
        button_frame.pack()

        self._build_action_button(
            button_frame,
            text="PAUSE",
            background="#cc8800",
            active_background="#ffaa00",
            command=self._do_pause,
            column=0,
        )
        self._build_action_button(
            button_frame,
            text="STOP",
            background="#aa2200",
            active_background="#dd3300",
            command=self._do_stop,
            column=1,
        )
        self._build_action_button(
            button_frame,
            text="KILL",
            background="#660000",
            active_background="#880000",
            command=self._do_kill,
            column=2,
        )

        self.resume_button = tk.Button(
            self,
            text="RESUME",
            font=("Courier New", 10, "bold"),
            fg="#ffffff",
            bg="#1a4a1a",
            activebackground="#2a6a2a",
            width=14,
            height=1,
            bd=0,
            state="disabled",
            command=self._do_resume,
        )
        self.resume_button.pack(pady=(16, 0))

        tk.Label(
            self,
            text="Event Log",
            font=("Courier New", 8),
            fg="#444444",
            bg=BG_COLOR,
        ).pack(anchor="w", padx=20, pady=(12, 2))

        self.log_box = tk.Text(
            self,
            height=5,
            font=("Courier New", 7),
            fg="#888888",
            bg=PANEL_COLOR,
            bd=0,
            state="disabled",
        )
        self.log_box.pack(fill="x", padx=20, pady=(0, 10))

    def _build_action_button(
        self,
        parent: tk.Widget,
        *,
        text: str,
        background: str,
        active_background: str,
        command,
        column: int,
    ) -> None:
        tk.Button(
            parent,
            text=text,
            font=("Courier New", 11, "bold"),
            fg="#ffffff",
            bg=background,
            activebackground=active_background,
            width=10,
            height=2,
            bd=0,
            command=command,
        ).grid(row=0, column=column, padx=8)

    def _confirm(self, title: str, prompt: str) -> bool:
        return messagebox.askyesno(title, prompt)

    def _do_pause(self) -> None:
        if not self._confirm("Confirm", "Pause the system?"):
            return
        threading.Thread(
            target=self.ks.pause,
            args=("Operator pause via GUI",),
            daemon=True,
        ).start()

    def _do_stop(self) -> None:
        if not self._confirm("Confirm", "Stop the system cleanly?\nState will be saved."):
            return
        threading.Thread(
            target=self.ks.stop,
            args=("Operator stop via GUI",),
            daemon=True,
        ).start()

    def _do_kill(self) -> None:
        if not self._confirm(
            "Hard Kill",
            "Hard kill the system?\n\nNo state will be saved.\nThis cannot be undone.",
        ):
            return
        self.ks.kill("Operator kill via GUI")

    def _do_resume(self) -> None:
        self.ks.resume()

    def _poll_state(self) -> None:
        state = self.ks.state
        if state.triggered:
            if state.level == StopLevel.PAUSE:
                self.status_label.config(text="PAUSED", fg=TEXT_STATUS_WARN)
                self.resume_button.config(state="normal")
            elif state.level == StopLevel.STOP:
                self.status_label.config(text="STOPPED", fg=TEXT_STATUS_STOP)
                self.resume_button.config(state="disabled")
            elif state.level == StopLevel.KILL:
                self.status_label.config(text="KILLED", fg=TEXT_STATUS_KILL)
                self.resume_button.config(state="disabled")
        else:
            self.status_label.config(text="RUNNING", fg=TEXT_STATUS_OK)
            self.resume_button.config(state="disabled")

        if state.log:
            self.log_box.config(state="normal")
            self.log_box.delete("1.0", tk.END)
            self.log_box.insert(tk.END, "\n".join(state.log[-6:]))
            self.log_box.see(tk.END)
            self.log_box.config(state="disabled")

        self.after(500, self._poll_state)


if __name__ == "__main__":
    app = KillSwitchPanel()
    app.mainloop()
