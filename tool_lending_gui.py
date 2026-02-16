"""
Tool Lending Tracker
Modern Matrix-style UI for tracking borrowed tools.
"""
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from ctypes import windll, byref, c_int

import sys

# ─── Configuration ───────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    application_path = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    application_path = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(application_path, "tool_lending_data.json")
LOG_FILE = os.path.join(application_path, "tool_lending_history.log")

# Colors - Modern Matrix with gradient feel
COLORS = {
    "bg_dark": "#0a0f0a",
    "bg_panel": "#0d1a0d",
    "bg_input": "#0a140a",
    "accent_green": "#00FF41",
    "accent_light": "#40FF70",
    "accent_dim": "#1a3a1a",
    "text_bright": "#00FF41",
    "text_dim": "#4a8a4a",
    "danger": "#FF4136",
    "border": "#1a4a1a",
}

FONT_FAMILY = "Consolas"

# ─── Data Management ─────────────────────────────────────────────────────────
def load_data():
    """Load data from JSON file or return defaults."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"tools": [], "borrowers": [], "loans": []}

def save_data(data):
    """Save data to JSON file."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def log_action(action, tool, borrower):
    """Log lending/return action to history file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {action}: {tool} -> {borrower}\n")

# ─── Title Bar Customization ─────────────────────────────────────────────────
def set_title_bar_color(window, bg_color, text_color):
    """Change title bar color on Windows 11."""
    try:
        hwnd = windll.user32.GetParent(window.winfo_id())
        
        def hex_to_colorref(hex_str):
            hex_str = hex_str.strip('#')
            r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            return r | (g << 8) | (b << 16)

        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR = 36

        bg = hex_to_colorref(bg_color)
        text = hex_to_colorref(text_color)

        windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, byref(c_int(bg)), 4)
        windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_TEXT_COLOR, byref(c_int(text)), 4)
    except Exception:
        pass

# ─── Custom Widgets ──────────────────────────────────────────────────────────
class GlowButton(tk.Canvas):
    """Button with hover glow effect."""
    def __init__(self, parent, text, command, width=120, height=32, 
                 bg=COLORS["accent_dim"], fg=COLORS["accent_green"], 
                 hover_bg=COLORS["accent_green"], hover_fg=COLORS["bg_dark"], **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg=COLORS["bg_panel"], highlightthickness=0, **kwargs)
        
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.bg = bg
        self.fg = fg
        self.hover_bg = hover_bg
        self.hover_fg = hover_fg
        self.current_bg = bg
        self.current_fg = fg
        
        self._draw()
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        
    def _draw(self):
        self.delete("all")
        # Rounded rectangle
        r = 6
        self.create_polygon(
            r, 0, self.width-r, 0, 
            self.width, r, self.width, self.height-r,
            self.width-r, self.height, r, self.height,
            0, self.height-r, 0, r,
            fill=self.current_bg, outline=self.current_bg, smooth=True
        )
        self.create_text(self.width//2, self.height//2, text=self.text, 
                        fill=self.current_fg, font=(FONT_FAMILY, 10, "bold"))
        
    def _on_enter(self, e):
        self.current_bg = self.hover_bg
        self.current_fg = self.hover_fg
        self._draw()
        
    def _on_leave(self, e):
        self.current_bg = self.bg
        self.current_fg = self.fg
        self._draw()
        
    def _on_click(self, e):
        if self.command:
            self.command()

class DangerButton(GlowButton):
    """Red danger button for delete operations."""
    def __init__(self, parent, text, command, width=80, height=28, **kwargs):
        super().__init__(parent, text, command, width, height,
                        bg="#2a1515", fg=COLORS["danger"],
                        hover_bg=COLORS["danger"], hover_fg="#ffffff", **kwargs)

class SearchEntry(tk.Frame):
    """Custom search entry with a popdown listbox (Original Stable Version)."""
    def __init__(self, parent, full_list, font, width, **kwargs):
        super().__init__(parent, bg=COLORS["bg_panel"], **kwargs)
        self.full_list = full_list
        self.filtered_list = full_list
        
        self.var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var, font=font, width=width,
                             bg=COLORS["bg_input"], fg=COLORS["text_bright"],
                             insertbackground=COLORS["accent_green"], bd=0,
                             highlightthickness=1, highlightbackground=COLORS["border"],
                             highlightcolor=COLORS["accent_green"])
        self.entry.pack(fill="x", expand=True, ipady=3)
        
        self.popdown = None
        self.listbox = None
        
        # Original Bindings + Click Improvement
        self.entry.bind("<KeyRelease>", self._on_key)
        self.entry.bind("<Button-1>", self._on_click)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Down>", self._on_arrow_down)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Escape>", self._hide_popdown)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def _on_click(self, event):
        """Show full list on click."""
        self.filtered_list = self.full_list
        if self.filtered_list:
            self._show_popdown()

    def _on_key(self, event):
        if hasattr(event, "keysym") and event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return
            
        value = self.get().lower()
        if value == "":
            self.filtered_list = self.full_list
        else:
            self.filtered_list = [item for item in self.full_list if value in item.lower()]
            
        if self.filtered_list:
            self._show_popdown()
        else:
            self._hide_popdown()

    def _show_popdown(self):
        if not self.popdown:
            self.popdown = tk.Toplevel(self)
            self.popdown.wm_overrideredirect(True)
            self.popdown.attributes("-topmost", True)
            
            # Use a frame to hold listbox and scrollbar
            self.pop_frame = tk.Frame(self.popdown, bg=COLORS["bg_input"], bd=1, relief="solid")
            self.pop_frame.pack(fill="both", expand=True)

            self.listbox = tk.Listbox(self.pop_frame, bg=COLORS["bg_input"], 
                                     fg=COLORS["text_bright"],
                                     font=self.entry["font"], bd=0,
                                     highlightthickness=0,
                                     selectbackground=COLORS["accent_dim"],
                                     selectforeground=COLORS["accent_green"])
            self.scrollbar = ttk.Scrollbar(self.pop_frame, orient="vertical", 
                                         command=self.listbox.yview,
                                         style="Vertical.TScrollbar")
            
            self.listbox.configure(yscrollcommand=self.scrollbar.set)
            
            self.listbox.pack(side="left", fill="both", expand=True)
            self.listbox.bind("<Button-1>", self._on_list_click)

        self.listbox.delete(0, tk.END)
        for item in self.filtered_list:
            self.listbox.insert(tk.END, item)
            
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = self.entry.winfo_width()
        
        # Calculate height: ~25 pixels per item, min 1, max 10 items
        item_count = len(self.filtered_list)
        item_height = 25 # Estimated height per row including padding
        
        if item_count > 10:
            h = 10 * item_height
            self.scrollbar.pack(side="right", fill="y")
        else:
            h = max(1, item_count) * item_height
            self.scrollbar.pack_forget()

        self.popdown.wm_geometry(f"{w}x{h}+{x}+{y}")
        self.popdown.deiconify()

    def _hide_popdown(self, event=None):
        if self.popdown:
            self.popdown.withdraw()

    def _on_list_click(self, event):
        # We can keep 'nearest' for better selection accuracy as it's transparent to the user
        index = self.listbox.nearest(event.y)
        if index >= 0:
            item = self.listbox.get(index)
            self.set(item)
            self._hide_popdown()
            self.entry.focus_set()

    def _on_arrow_down(self, event):
        if self.popdown and self.listbox:
            self.listbox.focus_set()
            self.listbox.activate(0)
            self.listbox.selection_set(0)

    def _on_enter(self, event):
        if self.popdown and self.popdown.winfo_viewable():
            selection = self.listbox.curselection()
            if selection:
                item = self.listbox.get(selection[0])
                self.set(item)
                self._hide_popdown()
            elif self.filtered_list:
                self.set(self.filtered_list[0])
                self._hide_popdown()
        
    def _on_focus_out(self, event):
        # Use a small delay to see where focus goes
        self.after(200, self._check_focus)

    def _check_focus(self):
        if not self.popdown:
            return
        try:
            # Check what currently has focus
            focused = self.winfo_toplevel().focus_get()
            
            # If focus is on the entry or within the popdown, don't hide
            if focused == self.entry:
                return
            
            # Traverse up from focused widget to see if it belongs to popdown
            curr = focused
            while curr:
                if curr == self.popdown:
                    return # Focus is inside popdown (listbox or scrollbar)
                try:
                    curr = curr.master
                except:
                    break
                    
            self._hide_popdown()
        except Exception:
            # In case of error (e.g. widget destroyed), default to hiding
            self._hide_popdown()

# ─── Main Application ────────────────────────────────────────────────────────
class ToolLendingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔧 Tool Lending Tracker")
        self.root.geometry("680x650")
        self.root.configure(bg=COLORS["bg_dark"])
        self.root.resizable(False, False)
        
        # Apply dark title bar
        self.root.update_idletasks()
        set_title_bar_color(self.root, COLORS["bg_dark"], COLORS["accent_green"])
        
        # Load data
        self.data = load_data()
        
        # Build UI
        self._setup_validation()
        self._create_header()
        self._create_management_section()
        self._create_lending_section()
        self._create_borrowed_section()
        
        # Populate lists
        self._refresh_all()
        
    def _setup_validation(self):
        """Setup input validation for character limits."""
        self.vcmd = (self.root.register(self._validate_input), '%P')

    def _validate_input(self, new_text):
        """Limit input to 30 characters."""
        return len(new_text) <= 30

    def _create_header(self):
        """Create app header with gradient effect."""
        header = tk.Frame(self.root, bg=COLORS["bg_dark"], height=60)
        header.pack(fill="x", padx=20, pady=(15, 5))
        header.pack_propagate(False)
        
        # Title with glow effect
        title = tk.Label(header, text="⚡ TOOL LENDING TRACKER", 
                        font=(FONT_FAMILY, 18, "bold"),
                        bg=COLORS["bg_dark"], fg=COLORS["accent_green"])
        title.pack(side="left")
        
        # Subtitle
        subtitle = tk.Label(header, text="Track your borrowed tools", 
                           font=(FONT_FAMILY, 10),
                           bg=COLORS["bg_dark"], fg=COLORS["text_dim"])
        subtitle.pack(side="left", padx=(15, 0), pady=(8, 0))
        
    def _create_management_section(self):
        """Create tools and borrowers management panels."""
        container = tk.Frame(self.root, bg=COLORS["bg_dark"])
        container.pack(fill="x", padx=20, pady=10)
        
        # ─── Tools Panel ─────────────────────────────────────────────────────
        tools_panel = tk.LabelFrame(container, text=" 🔧 TOOLS ", 
                                   font=(FONT_FAMILY, 11, "bold"),
                                   bg=COLORS["bg_panel"], fg=COLORS["accent_green"],
                                   bd=1, relief="solid")
        tools_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Tools listbox
        tools_frame = tk.Frame(tools_panel, bg=COLORS["bg_panel"])
        tools_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        self.tools_listbox = tk.Listbox(tools_frame, height=6, 
                                        bg=COLORS["bg_input"], fg=COLORS["text_bright"],
                                        font=(FONT_FAMILY, 10), 
                                        selectbackground=COLORS["accent_dim"],
                                        selectforeground=COLORS["accent_green"],
                                        bd=0, highlightthickness=1,
                                        highlightcolor=COLORS["border"],
                                        highlightbackground=COLORS["border"])
        self.tools_listbox.pack(fill="both", expand=True)
        
        # Add tool input
        add_tools_frame = tk.Frame(tools_panel, bg=COLORS["bg_panel"])
        add_tools_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.tool_entry = tk.Entry(add_tools_frame, bg=COLORS["bg_input"], 
                                  fg=COLORS["text_bright"], 
                                  insertbackground=COLORS["accent_green"],
                                  font=(FONT_FAMILY, 10), bd=0,
                                  highlightthickness=1,
                                  highlightcolor=COLORS["accent_green"],
                                  highlightbackground=COLORS["border"],
                                  validate="key", validatecommand=self.vcmd)
        self.tool_entry.pack(side="left", fill="x", expand=True, ipady=5)
        self.tool_entry.bind("<Return>", lambda e: self._add_tool())
        self.tools_listbox.bind("<Delete>", lambda e: self._delete_tool())
        
        add_tool_btn = GlowButton(add_tools_frame, "+", self._add_tool, width=40, height=28)
        add_tool_btn.pack(side="left", padx=(5, 0))
        
        # Delete tool button
        del_tool_btn = DangerButton(tools_panel, "🗑 Delete", self._delete_tool, width=90)
        del_tool_btn.pack(pady=(0, 10))
        
        # ─── Borrowers Panel ─────────────────────────────────────────────────
        borrowers_panel = tk.LabelFrame(container, text=" 👤 BORROWERS ", 
                                       font=(FONT_FAMILY, 11, "bold"),
                                       bg=COLORS["bg_panel"], fg=COLORS["accent_green"],
                                       bd=1, relief="solid")
        borrowers_panel.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        # Borrowers listbox
        borrowers_frame = tk.Frame(borrowers_panel, bg=COLORS["bg_panel"])
        borrowers_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        self.borrowers_listbox = tk.Listbox(borrowers_frame, height=6,
                                            bg=COLORS["bg_input"], fg=COLORS["text_bright"],
                                            font=(FONT_FAMILY, 10),
                                            selectbackground=COLORS["accent_dim"],
                                            selectforeground=COLORS["accent_green"],
                                            bd=0, highlightthickness=1,
                                            highlightcolor=COLORS["border"],
                                            highlightbackground=COLORS["border"])
        self.borrowers_listbox.pack(fill="both", expand=True)
        
        # Add borrower input
        add_borrowers_frame = tk.Frame(borrowers_panel, bg=COLORS["bg_panel"])
        add_borrowers_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.borrower_entry = tk.Entry(add_borrowers_frame, bg=COLORS["bg_input"],
                                      fg=COLORS["text_bright"],
                                      insertbackground=COLORS["accent_green"],
                                      font=(FONT_FAMILY, 10), bd=0,
                                      highlightthickness=1,
                                      highlightcolor=COLORS["accent_green"],
                                      highlightbackground=COLORS["border"],
                                      validate="key", validatecommand=self.vcmd)
        self.borrower_entry.pack(side="left", fill="x", expand=True, ipady=5)
        self.borrower_entry.bind("<Return>", lambda e: self._add_borrower())
        self.borrowers_listbox.bind("<Delete>", lambda e: self._delete_borrower())
        
        add_borrower_btn = GlowButton(add_borrowers_frame, "+", self._add_borrower, width=40, height=28)
        add_borrower_btn.pack(side="left", padx=(5, 0))
        
        # Delete borrower button
        del_borrower_btn = DangerButton(borrowers_panel, "🗑 Delete", self._delete_borrower, width=90)
        del_borrower_btn.pack(pady=(0, 10))
        
    def _create_lending_section(self):
        """Create lending controls using custom searchable entries."""
        lending_frame = tk.LabelFrame(self.root, text=" 🔐 LEND TOOL ", 
                                     font=(FONT_FAMILY, 12, "bold"),
                                     bg=COLORS["bg_panel"], fg=COLORS["accent_green"],
                                     bd=2, relief="solid")
        lending_frame.pack(fill="x", padx=20, pady=15)
        
        inner = tk.Frame(lending_frame, bg=COLORS["bg_panel"])
        inner.pack(fill="x", padx=15, pady=10)
        
        # Row 0: Labels
        tk.Label(inner, text="Tool:", font=(FONT_FAMILY, 10, "bold"),
                bg=COLORS["bg_panel"], fg=COLORS["text_dim"]).grid(row=0, column=0, sticky="w", padx=5)
        
        tk.Label(inner, text="Borrower:", font=(FONT_FAMILY, 10, "bold"),
                bg=COLORS["bg_panel"], fg=COLORS["text_dim"]).grid(row=0, column=1, sticky="w", padx=5)
        
        # Row 1: Custom Search Entries
        self.tool_search = SearchEntry(inner, [], (FONT_FAMILY, 10), width=35)
        self.tool_search.grid(row=1, column=0, sticky="we", padx=5, pady=(2, 10))
        
        self.borrower_search = SearchEntry(inner, [], (FONT_FAMILY, 10), width=35)
        self.borrower_search.grid(row=1, column=1, sticky="we", padx=5, pady=(2, 10))
        
        # Lend button
        lend_btn = GlowButton(inner, "🔐 LEND", self._lend_tool, 
                             width=100, height=32,
                             bg=COLORS["accent_dim"], fg=COLORS["accent_light"],
                             hover_bg=COLORS["accent_green"], hover_fg=COLORS["bg_dark"])
        lend_btn.grid(row=0, column=2, rowspan=2, padx=(15, 0), sticky="e")
        
        inner.columnconfigure(0, weight=1)
        inner.columnconfigure(1, weight=1)
        
        # Scrollbar styling (for other parts of UI)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar",
                       background=COLORS["accent_dim"],
                       troughcolor=COLORS["bg_input"],
                       bordercolor=COLORS["border"],
                       arrowcolor=COLORS["accent_green"],
                       lightcolor=COLORS["accent_dim"],
                       darkcolor=COLORS["bg_dark"])
        
        style.map("Vertical.TScrollbar",
                 background=[("active", COLORS["accent_green"]), ("pressed", COLORS["accent_green"])])
        
    def _create_borrowed_section(self):
        """Create currently borrowed items list."""
        borrowed_frame = tk.LabelFrame(self.root, text=" 📋 CURRENTLY BORROWED ", 
                                      font=(FONT_FAMILY, 12, "bold"),
                                      bg=COLORS["bg_panel"], fg=COLORS["accent_green"],
                                      bd=2, relief="solid")
        borrowed_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Scrollable frame for borrowed items
        self.borrowed_canvas = tk.Canvas(borrowed_frame, bg=COLORS["bg_panel"], 
                          highlightthickness=0, height=180)
        scrollbar = ttk.Scrollbar(borrowed_frame, orient="vertical", 
                                  command=self.borrowed_canvas.yview,
                                  style="Vertical.TScrollbar")
        
        self.borrowed_container = tk.Frame(self.borrowed_canvas, bg=COLORS["bg_panel"])
        
        self.borrowed_container.bind(
            "<Configure>",
            lambda e: self.borrowed_canvas.configure(scrollregion=self.borrowed_canvas.bbox("all"))
        )
        
        self.borrowed_canvas.create_window((0, 0), window=self.borrowed_container, anchor="nw")
        self.borrowed_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.borrowed_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Enable mouse wheel scrolling
        self.borrowed_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for the borrowed canvas."""
        # Only scroll if the mouse is over the canvas area
        x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
        widget = self.root.winfo_containing(x, y)
        
        # Check if the widget under cursor is the canvas or one of its descendants
        path = str(widget) if widget else ""
        if str(self.borrowed_canvas) in path:
            self.borrowed_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def _refresh_all(self):
        """Refresh all UI elements with current data."""
        # Refresh tools list
        self.tools_listbox.delete(0, tk.END)
        for tool in self.data["tools"]:
            self.tools_listbox.insert(tk.END, tool)
            
        # Refresh borrowers list
        self.borrowers_listbox.delete(0, tk.END)
        for borrower in self.data["borrowers"]:
            self.borrowers_listbox.insert(tk.END, borrower)
            
        # Refresh Search Entries - only show tools NOT currently borrowed, and filter empty strings
        borrowed_tools = {loan["tool"] for loan in self.data["loans"]}
        available_tools = [t for t in self.data["tools"] if t and t.strip() and t not in borrowed_tools]
        available_borrowers = [b for b in self.data["borrowers"] if b and b.strip()]
        
        self.tool_search.full_list = available_tools
        self.borrower_search.full_list = available_borrowers
        
        # Refresh borrowed items
        for widget in self.borrowed_container.winfo_children():
            widget.destroy()
            
        if not self.data["loans"]:
            no_items = tk.Label(self.borrowed_container, 
                               text="No items currently borrowed",
                               font=(FONT_FAMILY, 10, "italic"),
                               bg=COLORS["bg_panel"], fg=COLORS["text_dim"])
            no_items.pack(pady=20)
        else:
            for i, loan in enumerate(self.data["loans"]):
                self._create_borrowed_item(loan, i)
                
    def _create_borrowed_item(self, loan, index):
        """Create a single borrowed item row."""
        row = tk.Frame(self.borrowed_container, bg=COLORS["bg_input"], 
                      highlightthickness=1, highlightbackground=COLORS["border"])
        row.pack(fill="x", padx=5, pady=3)
        
        # Tool name
        tk.Label(row, text=f"🔧 {loan['tool']}", 
                font=(FONT_FAMILY, 10, "bold"),
                bg=COLORS["bg_input"], fg=COLORS["accent_green"],
                width=16, anchor="w", wraplength=130, justify="left").pack(side="left", padx=(5, 5), pady=8)
        
        # Arrow
        tk.Label(row, text="→", font=(FONT_FAMILY, 12),
                bg=COLORS["bg_input"], fg=COLORS["text_dim"]).pack(side="left", padx=2)
        
        # Borrower name
        tk.Label(row, text=f"👤 {loan['borrower']}", 
                font=(FONT_FAMILY, 10),
                bg=COLORS["bg_input"], fg=COLORS["accent_light"],
                width=16, anchor="w", wraplength=130, justify="left").pack(side="left", padx=5, pady=8)
        
        # Date
        tk.Label(row, text=f"📅 {loan['date']}", 
                font=(FONT_FAMILY, 9),
                bg=COLORS["bg_input"], fg=COLORS["text_dim"]).pack(side="left", padx=10)
        
        # Return button
        return_btn = GlowButton(row, "↩ Return", 
                               lambda l=loan: self._return_tool(l),
                               width=80, height=26,
                               bg="#1a2a1a", fg=COLORS["accent_green"],
                               hover_bg=COLORS["accent_green"], hover_fg=COLORS["bg_dark"])
        return_btn.pack(side="right", padx=10, pady=5)
        
    def _add_tool(self):
        """Add a new tool."""
        name = self.tool_entry.get().strip()
        if not name:
            return
        if name in self.data["tools"]:
            messagebox.showwarning("Warning", f"Tool '{name}' already exists!")
            return
        self.data["tools"].append(name)
        save_data(self.data)
        self.tool_entry.delete(0, tk.END)
        self._refresh_all()
        
    def _delete_tool(self):
        """Delete selected tool."""
        selection = self.tools_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Select a tool to delete.")
            return
        tool = self.tools_listbox.get(selection[0])
        
        # Check if currently borrowed
        if any(loan["tool"] == tool for loan in self.data["loans"]):
            messagebox.showwarning("Warning", f"Cannot delete '{tool}' - it is currently borrowed!")
            return
            
        if messagebox.askyesno("Confirm", f"Delete tool '{tool}'?"):
            self.data["tools"].remove(tool)
            save_data(self.data)
            self._refresh_all()
            
    def _add_borrower(self):
        """Add a new borrower."""
        name = self.borrower_entry.get().strip()
        if not name:
            return
        if name in self.data["borrowers"]:
            messagebox.showwarning("Warning", f"Borrower '{name}' already exists!")
            return
        self.data["borrowers"].append(name)
        save_data(self.data)
        self.borrower_entry.delete(0, tk.END)
        self._refresh_all()
        
    def _delete_borrower(self):
        """Delete selected borrower."""
        selection = self.borrowers_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Select a borrower to delete.")
            return
        borrower = self.borrowers_listbox.get(selection[0])
        
        # Check if has active loans
        if any(loan["borrower"] == borrower for loan in self.data["loans"]):
            messagebox.showwarning("Warning", f"Cannot delete '{borrower}' - has active loans!")
            return
            
        if messagebox.askyesno("Confirm", f"Delete borrower '{borrower}'?"):
            self.data["borrowers"].remove(borrower)
            save_data(self.data)
            self._refresh_all()
            
    def _lend_tool(self):
        """Create a new loan."""
        tool = self.tool_search.get().strip()
        borrower = self.borrower_search.get().strip()
        
        if not tool or not borrower:
            messagebox.showwarning("Warning", "Select/Enter both a tool and a borrower!")
            return
            
        # Validate that the typed tool and borrower actually exist
        if tool not in self.data["tools"]:
            messagebox.showerror("Error", f"Invalid tool: '{tool}'\nPlease add it first or select from the list.")
            return
        if borrower not in self.data["borrowers"]:
            messagebox.showerror("Error", f"Invalid borrower: '{borrower}'\nPlease add them first or select from the list.")
            return
            
        # Check if already borrowed
        if any(loan["tool"] == tool for loan in self.data["loans"]):
            messagebox.showwarning("Warning", f"Tool '{tool}' is already borrowed!")
            return
            
        loan = {
            "tool": tool,
            "borrower": borrower,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        self.data["loans"].append(loan)
        save_data(self.data)
        log_action("LEND", tool, borrower)
        
        # Clear selections
        self.tool_search.set("")
        self.borrower_search.set("")
        self._refresh_all()
        
    def _return_tool(self, loan):
        """Return a borrowed tool."""
        if messagebox.askyesno("Confirm", f"Return '{loan['tool']}' from {loan['borrower']}?"):
            self.data["loans"].remove(loan)
            save_data(self.data)
            log_action("RETURN", loan["tool"], loan["borrower"])
            self._refresh_all()

# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = ToolLendingApp(root)
    root.mainloop()
