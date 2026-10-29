import json
import re
import webbrowser
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urlparse
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Librerie per le richieste web
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None


# =========================
# CONFIGURAZIONE
# =========================

APP_NAME = "WebDesk"

DATA_DIR = Path.home() / ".webdesk"
HISTORY_FILE = DATA_DIR / "history.json"

ENGINES = {
    "Google": "https://www.google.com/search?q=",
    "Bing": "https://www.bing.com/search?q=",
    "DuckDuckGo": "https://duckduckgo.com/?q="
}

BG = "#f3f5fa"
PANEL = "#ffffff"
ACCENT = "#5146e5"
TEXT = "#20243a"
MUTED = "#72778a"
BORDER = "#e2e5ef"


# =========================
# APPLICAZIONE
# =========================

class WebDesk:

    def __init__(self, root):
        self.root = root
        self.root.title("WebDesk | Ricerca Web")
        self.root.geometry("1100x720")
        self.root.minsize(850, 570)
        self.root.configure(bg=BG)

        self.mode = "Ricerca web"
        self.history = self.load_history()

        self.configure_style()
        self.create_interface()

        self.log("Benvenuto in WebDesk!", "title")
        self.log(
            "Cerca sul web, trova documenti pubblici "
            "e avvia ricerche mirate sui siti.",
            "normal"
        )
        self.log(
            "Seleziona una funzione dal menu laterale "
            "e inserisci una ricerca in basso.",
            "muted"
        )

    # =========================
    # STILE
    # =========================

    def configure_style(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TFrame",
            background=BG
        )

        style.configure(
            "TLabel",
            background=BG,
            foreground=TEXT,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 23, "bold"),
            foreground=TEXT
        )

        style.configure(
            "Subtitle.TLabel",
            foreground=MUTED
        )

        style.configure(
            "TEntry",
            padding=10
        )

        style.configure(
            "TCombobox",
            padding=7
        )

        style.configure(
            "TButton",
            padding=9,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="white",
            padding=12,
            font=("Segoe UI", 10, "bold")
        )

        style.map(
            "Accent.TButton",
            background=[("active", "#4035c5")]
        )

    # =========================
    # INTERFACCIA
    # =========================

    def create_interface(self):

        header = ttk.Frame(
            self.root,
            padding=(25, 20, 25, 12)
        )
        header.pack(fill="x")

        ttk.Label(
            header,
            text="WebDesk",
            style="Title.TLabel"
        ).pack(side="left")

        ttk.Label(
            header,
            text="  Ricerca intelligente sul Web",
            style="Subtitle.TLabel"
        ).pack(side="left", padx=12, pady=(10, 0))

        self.engine = tk.StringVar(value="Google")

        engine_box = ttk.Combobox(
            header,
            textvariable=self.engine,
            values=list(ENGINES.keys()),
            state="readonly",
            width=16
        )

        engine_box.pack(side="right", pady=8)

        # Area principale
        main = ttk.Frame(
            self.root,
            padding=(25, 5, 25, 15)
        )

        main.pack(fill="both", expand=True)

        # Menu laterale
        sidebar = tk.Frame(
            main,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            width=225
        )

        sidebar.pack(
            side="left",
            fill="y",
            padx=(0, 18)
        )

        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="STRUMENTI",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=16, pady=(18, 12))

        features = [
            ("⌕", "Ricerca web"),
            ("▤", "File per estensione"),
            ("◎", "Analisi sito"),
            ("▧", "Immagini"),
            ("▣", "Notizie"),
            ("↗", "Ricerca link"),
            ("⌘", "Metadati"),
            ("◷", "Cronologia"),
            ("⇩", "Esporta cronologia")
        ]

        self.mode_buttons = {}

        for icon, name in features:

            button = tk.Button(
                sidebar,
                text=f"  {icon}    {name}",
                anchor="w",
                bg=PANEL,
                fg=TEXT,
                activebackground="#eeeeff",
                activeforeground=ACCENT,
                relief="flat",
                bd=0,
                padx=10,
                pady=10,
                cursor="hand2",
                font=("Segoe UI", 10),
                command=lambda m=name: self.set_mode(m)
            )

            button.pack(fill="x", padx=7, pady=1)
            self.mode_buttons[name] = button

        tk.Frame(
            sidebar,
            bg=BORDER,
            height=1
        ).pack(fill="x", padx=15, pady=15)

        tk.Label(
            sidebar,
            text="ESEMPIO",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=16)

        tk.Label(
            sidebar,
            text="pdf manuale Windows\n\n"
                 "example.com\n\n"
                 "immagini computer",
            bg=PANEL,
            fg=TEXT,
            justify="left",
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=16, pady=10)

        # Pannello destro
        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        self.page_title = ttk.Label(
            right,
            text="Ricerca web",
            font=("Segoe UI", 17, "bold")
        )

        self.page_title.pack(anchor="w", pady=(4, 4))

        self.description = ttk.Label(
            right,
            text="Cerca pagine web usando il motore selezionato.",
            style="Subtitle.TLabel"
        )

        self.description.pack(anchor="w", pady=(0, 14))

        # Scheda risultati
        card = tk.Frame(
            right,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        card.pack(fill="both", expand=True)

        card_header = tk.Frame(card, bg=PANEL)
        card_header.pack(fill="x", padx=18, pady=15)

        tk.Label(
            card_header,
            text="Attività e risultati",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 11, "bold")
        ).pack(side="left")

        ttk.Button(
            card_header,
            text="Pulisci",
            command=self.clear_output
        ).pack(side="right")

        output_frame = tk.Frame(card, bg=PANEL)
        output_frame.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 15)
        )

        self.output = tk.Text(
            output_frame,
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 10),
            wrap="word",
            relief="flat",
            padx=5,
            pady=5,
            state="disabled"
        )

        scrollbar = ttk.Scrollbar(
            output_frame,
            orient="vertical",
            command=self.output.yview
        )

        self.output.configure(
            yscrollcommand=scrollbar.set
        )

        self.output.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.output.tag_configure(
            "title",
            font=("Segoe UI", 14, "bold")
        )

        self.output.tag_configure(
            "muted",
            foreground=MUTED
        )

        self.output.tag_configure(
            "success",
            foreground="#168044"
        )

        self.output.tag_configure(
            "link",
            foreground=ACCENT,
            underline=True
        )

        # Barra di ricerca inferiore
        dock = tk.Frame(
            self.root,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        dock.pack(
            fill="x",
            padx=25,
            pady=(0, 20)
        )

        # Pulsante a 9 puntini
        self.features_button = ttk.Button(
            dock,
            text="⠿",
            width=4,
            command=self.show_features
        )

        self.features_button.pack(
            side="left",
            padx=(10, 5),
            pady=10
        )

        self.query = tk.StringVar()

        self.search_entry = ttk.Entry(
            dock,
            textvariable=self.query,
            font=("Segoe UI", 12)
        )

        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=8,
            pady=12
        )

        self.search_entry.bind(
            "<Return>",
            lambda event: self.submit()
        )

        self.search_entry.bind(
            "<FocusIn>",
            self.remove_placeholder
        )

        self.placeholder = "Scrivi cosa vuoi cercare..."

        self.search_entry.insert(0, self.placeholder)
        self.search_entry.configure(foreground=MUTED)

        self.search_entry.bind(
            "<FocusOut>",
            self.restore_placeholder
        )

        ttk.Button(
            dock,
            text="Invia  →",
            style="Accent.TButton",
            command=self.submit
        ).pack(side="right", padx=10, pady=8)

    # =========================
    # BARRA DI RICERCA
    # =========================

    def remove_placeholder(self, event=None):

        if self.query.get() == self.placeholder:
            self.search_entry.delete(0, "end")
            self.search_entry.configure(foreground=TEXT)

    def restore_placeholder(self, event=None):

        if not self.query.get().strip():
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, self.placeholder)
            self.search_entry.configure(foreground=MUTED)

    def get_query(self):
        value = self.query.get().strip()

        if value == self.placeholder:
            return ""

        return value

    # =========================
    # OUTPUT
    # =========================

    def log(self, text, tag="normal"):

        self.output.configure(state="normal")

        self.output.insert(
            "end",
            text + "\n",
            tag
        )

        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_output(self):

        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    # =========================
    # CRONOLOGIA
    # =========================

    def load_history(self):

        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            return data if isinstance(data, list) else []

        except (OSError, json.JSONDecodeError):
            return []

    def save_history(self):

        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            HISTORY_FILE.write_text(
                json.dumps(
                    self.history,
                    ensure_ascii=False,
                    indent=2
                ),
                encoding="utf-8"
            )

        except OSError as error:
            self.log(f"Errore salvataggio cronologia: {error}", "muted")

    def add_history(self, query, url):

        self.history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": self.mode,
            "engine": self.engine.get(),
            "query": query,
            "url": url
        })

        self.save_history()

    def show_history(self):

        if not self.history:
            self.log("La cronologia è vuota.", "muted")
            return

        for item in reversed(self.history):
            self.log(
                f"{item.get('time', '')} | "
                f"{item.get('engine', '')} | "
                f"{item.get('query', '')}"
            )

            self.log(
                item.get("url", ""),
                "link"
            )

    def export_history(self):

        if not self.history:
            messagebox.showinfo(
                "Cronologia",
                "Non ci sono ricerche da esportare."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Esporta cronologia",
            defaultextension=".txt",
            initialfile="webdesk_cronologia.txt",
            filetypes=[
                ("File di testo", "*.txt"),
                ("File JSON", "*.json")
            ]
        )

        if not path:
            return

        try:

            if path.lower().endswith(".json"):

                content = json.dumps(
                    self.history,
                    ensure_ascii=False,
                    indent=2
                )

            else:

                lines = []

                for item in self.history:
                    lines.append(
                        f"{item.get('time', '')} | "
                        f"{item.get('engine', '')} | "
                        f"{item.get('query', '')}\n"
                        f"{item.get('url', '')}\n"
                    )

                content = "\n".join(lines)

            Path(path).write_text(
                content,
                encoding="utf-8"
            )

            self.log(
                f"Cronologia esportata: {path}",
                "success"
            )

        except OSError as error:

            messagebox.showerror(
                "Errore",
                str(error)
            )

    # =========================
    # MENU FUNZIONI
    # =========================

    def show_features(self):

        menu = tk.Menu(
            self.root,
            tearoff=False,
            font=("Segoe UI", 10)
        )

        features = [
            "Ricerca web",
            "File per estensione",
            "Analisi sito",
            "Immagini",
            "Notizie",
            "Ricerca link",
            "Metadati",
            "Cronologia",
            "Esporta cronologia"
        ]

        for feature in features:
            menu.add_command(
                label=feature,
                command=lambda m=feature: self.set_mode(m)
            )

        try:
            menu.tk_popup(
                self.features_button.winfo_rootx(),
                self.features_button.winfo_rooty() - 10
            )
        finally:
            menu.grab_release()

    def set_mode(self, mode):

        self.mode = mode

        descriptions = {
            "Ricerca web": "Cerca pagine web.",
            "File per estensione": "Cerca file pubblicamente indicizzati.",
            "Analisi sito": "Cerca informazioni pubbliche su un dominio.",
            "Immagini": "Cerca immagini.",
            "Notizie": "Cerca notizie.",
            "Ricerca link": "Trova pagine e collegamenti correlati.",
            "Metadati": "Cerca pagine per titolo, URL e tipo di file.",
            "Cronologia": "Ricerche salvate localmente.",
            "Esporta cronologia": "Salva le ricerche in un file."
        }

        self.page_title.configure(text=mode)

        self.description.configure(
            text=descriptions.get(mode, "")
        )

        for name, button in self.mode_buttons.items():

            if name == mode:
                button.configure(
                    bg="#eeeeff",
                    fg=ACCENT,
                    font=("Segoe UI", 10, "bold")
                )

            else:
                button.configure(
                    bg=PANEL,
                    fg=TEXT,
                    font=("Segoe UI", 10)
                )

        self.log(f"\n--- {mode} ---", "title")

        if mode == "Cronologia":
            self.show_history()

        elif mode == "Esporta cronologia":
            self.log(
                "Premi Invia per esportare la cronologia.",
                "muted"
            )

        self.search_entry.focus_set()

    # =========================
    # MOTORI DI RICERCA
    # =========================

    def make_url(self, query, kind="web"):

        encoded = quote_plus(query)
        engine = self.engine.get()

        if kind == "images":

            if engine == "Bing":
                return "https://www.bing.com/images/search?q=" + encoded

            if engine == "DuckDuckGo":
                return (
                    "https://duckduckgo.com/?q="
                    + encoded
                    + "&iax=images&ia=images"
                )

            return (
                "https://www.google.com/search?tbm=isch&q="
                + encoded
            )

        if kind == "news":

            if engine == "Bing":
                return "https://www.bing.com/news/search?q=" + encoded

            if engine == "DuckDuckGo":
                return (
                    "https://duckduckgo.com/?q="
                    + encoded
                    + "&iar=news&ia=news"
                )

            return (
                "https://www.google.com/search?tbm=nws&q="
                + encoded
            )

        return ENGINES[engine] + encoded

    def open_search(self, query, kind="web"):

        url = self.make_url(query, kind)

        try:
            webbrowser.open_new_tab(url)

            self.add_history(query, url)

            self.log(
                f"Ricerca avviata con {self.engine.get()}:",
                "success"
            )

            self.log(query)
            self.log(url, "link")

        except Exception as error:

            self.log(
                f"Errore apertura browser: {error}",
                "muted"
            )

    # =========================
    # RICERCA FILE
    # =========================

    def search_files(self, query):

        parts = query.split(maxsplit=1)

        extension = parts[0].lstrip(".")
        terms = parts[1] if len(parts) > 1 else ""

        extension = re.sub(
            r"[^a-zA-Z0-9_-]",
            "",
            extension
        )

        if not extension:

            messagebox.showwarning(
                "Estensione non valida",
                "Esempio: pdf manuale Windows"
            )
            return

        self.open_search(
            f"filetype:{extension} {terms}".strip()
        )

    # =========================
    # ANALISI SITO
    # =========================

    def analyze_site(self, value):

        candidate = value.strip()

        if not candidate.startswith(("http://", "https://")):
            candidate = "https://" + candidate

        parsed = urlparse(candidate)
        domain = parsed.netloc or parsed.path.split("/")[0]

        if domain.startswith("www."):
            domain = domain[4:]

        if not domain or "." not in domain:

            messagebox.showwarning(
                "Dominio non valido",
                "Inserisci un dominio valido, ad esempio example.com"
            )
            return

        webbrowser.open_new_tab(candidate)

        self.log(
            f"Sito aperto: {candidate}",
            "success"
        )

        self.log(
            "Avvio ricerche pubbliche indicizzate. "
            "Non è una scansione completa del sito.",
            "muted"
        )

        self.open_search(f"site:{domain} informazioni")
        self.open_search(f"site:{domain} filetype:pdf")
        self.open_search(f"site:{domain} contatti OR documentazione")

    # =========================
    # INVIO
    # =========================

    def submit(self):

        if self.mode == "Cronologia":
            self.show_history()
            return

        if self.mode == "Esporta cronologia":
            self.export_history()
            return

        query = self.get_query()

        if not query:

            messagebox.showinfo(
                "WebDesk",
                "Scrivi qualcosa nella barra di ricerca."
            )
            return

        self.log(
            f"\n[{datetime.now().strftime('%H:%M:%S')}] "
            f"{self.mode}: {query}",
            "title"
        )

        if self.mode == "Analisi sito":
            self.analyze_site(query)

        elif self.mode == "File per estensione":
            self.search_files(query)

        elif self.mode == "Immagini":
            self.open_search(query, "images")

        elif self.mode == "Notizie":
            self.open_search(query, "news")

        elif self.mode == "Ricerca link":
            self.open_search(query + " link")

        elif self.mode == "Metadati":
            self.open_search(
                query + " (intitle OR inurl OR filetype)"
            )

        else:
            self.open_search(query)


# =========================
# AVVIO
# =========================

def main():

    root = tk.Tk()

    app = WebDesk(root)

    root.mainloop()


if __name__ == "__main__":
    main()