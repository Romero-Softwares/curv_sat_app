"""Dicas contextuais para widgets Tk/CustomTkinter."""

from __future__ import annotations

import ctypes
import tkinter as tk
from ctypes import wintypes


_TOOLTIP_MARGIN = 8


def _position_tooltip(
    anchor_x: int,
    anchor_y: int,
    anchor_width: int,
    anchor_height: int,
    tooltip_width: int,
    tooltip_height: int,
    work_area: tuple[int, int, int, int],
) -> tuple[int, int]:
    """Calcula uma posição visível, invertendo a dica perto das bordas."""
    left, top, right, bottom = work_area
    x = anchor_x + 12
    y = anchor_y + anchor_height + _TOOLTIP_MARGIN

    if x + tooltip_width > right - _TOOLTIP_MARGIN:
        x = anchor_x + anchor_width - tooltip_width - 12
    if y + tooltip_height > bottom - _TOOLTIP_MARGIN:
        y = anchor_y - tooltip_height - _TOOLTIP_MARGIN

    max_x = max(left + _TOOLTIP_MARGIN, right - tooltip_width - _TOOLTIP_MARGIN)
    max_y = max(top + _TOOLTIP_MARGIN, bottom - tooltip_height - _TOOLTIP_MARGIN)
    return (
        max(left + _TOOLTIP_MARGIN, min(x, max_x)),
        max(top + _TOOLTIP_MARGIN, min(y, max_y)),
    )


def _work_area(widget, x: int, y: int) -> tuple[int, int, int, int]:
    """Retorna a área útil do monitor que contém o widget, com fallback Tk."""
    if hasattr(ctypes, "windll"):
        try:
            class MonitorInfo(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            point = wintypes.POINT(x, y)
            monitor = ctypes.windll.user32.MonitorFromPoint(point, 2)
            info = MonitorInfo()
            info.cbSize = ctypes.sizeof(info)
            if monitor and ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                work = info.rcWork
                return work.left, work.top, work.right, work.bottom
        except (AttributeError, OSError):
            pass

    left = widget.winfo_vrootx()
    top = widget.winfo_vrooty()
    return left, top, left + widget.winfo_vrootwidth(), top + widget.winfo_vrootheight()


class Tooltip:
    """Exibe uma descrição curta quando o cursor permanece sobre um widget."""

    def __init__(self, widget, text: str, delay: int = 450) -> None:
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after_id = None
        self._window = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._cancel_schedule()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel_schedule(self) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        self._after_id = None
        if self._window is not None or not self.widget.winfo_exists():
            return
        self._window = tk.Toplevel(self.widget)
        self._window.wm_overrideredirect(True)
        self._window.wm_attributes("-topmost", True)
        self._window.withdraw()
        tk.Label(
            self._window,
            text=self.text,
            justify="left",
            background="#1f2937",
            foreground="#f8fafc",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=5,
            wraplength=300,
        ).pack()
        self._window.update_idletasks()

        anchor_x = self.widget.winfo_rootx()
        anchor_y = self.widget.winfo_rooty()
        x, y = _position_tooltip(
            anchor_x,
            anchor_y,
            self.widget.winfo_width(),
            self.widget.winfo_height(),
            self._window.winfo_reqwidth(),
            self._window.winfo_reqheight(),
            _work_area(self.widget, anchor_x, anchor_y),
        )
        self._window.wm_geometry(f"+{x}+{y}")
        self._window.deiconify()

    def _hide(self, _event=None) -> None:
        self._cancel_schedule()
        if self._window is not None:
            self._window.destroy()
            self._window = None


def add_tooltip(widget, text: str) -> Tooltip:
    """Vincula uma dica a ``widget`` e preserva sua referência enquanto ele existir."""
    tooltip = Tooltip(widget, text)
    widget._tooltip = tooltip
    return tooltip
