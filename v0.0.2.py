import json
import re
import webbrowser
import threading
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urljoin, urlparse as parse_url, parse_qs
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
APP_VERSION = "v0.0.2"

DATA_DIR = Path.home() / ".webdesk"
HISTORY_FILE = DATA_DIR / "history.json"

ENGINES = {
    "Google": "https://www.google.com/search?q=",
    "Bing": "https://www.bing.com/search?q=",
    "DuckDuckGo": "https://duckduckgo.com/?q=",
    "Yahoo": "https://search.yahoo.com/search?p="
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
        self.root.minsize(700, 500)
        self.root.resizable(True, True)
        self.root.configure(bg=BG)

        self.mode = "Ricerca web"
        self.history = self.load_history()

        self.configure_style()
        # Layout a griglia: intestazione in alto, contenuto elastico,
        # barra di ricerca sempre ancorata al bordo inferiore.
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_columnconfigure(0, weight=1)
        self.create_interface()
        self.root.bind("<Configure>", self.on_window_resize)

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
        header.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header,
            text="WebDesk",
            style="Title.TLabel"
        ).pack(side="left")

        self.header_subtitle = ttk.Label(
            header,
            text="  Ricerca intelligente sul Web",
            style="Subtitle.TLabel"
        )
        self.header_subtitle.pack(side="left", padx=12, pady=(10, 0))

        self.engine = tk.StringVar(value="Google")

        engine_box = ttk.Combobox(
            header,
            textvariable=self.engine,
            values=[*ENGINES.keys(), "Tutti i motori"],
            state="readonly",
            width=18
        )

        engine_box.pack(side="right", pady=8)

        # Area principale
        main = ttk.Frame(
            self.root,
            padding=(25, 5, 25, 15)
        )

        main.grid(row=1, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=0)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

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
        self.sidebar = sidebar

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
            ("⇩", "Esporta cronologia"),
            ("ⓘ", "About")
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

        # Pannello attività e risultati: intestazione, stato e area di lettura.
        card = tk.Frame(
            right,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        card.pack(fill="both", expand=True)

        card_header = tk.Frame(card, bg=PANEL)
        card_header.pack(fill="x", padx=20, pady=(17, 12))

        header_text = tk.Frame(card_header, bg=PANEL)
        header_text.pack(side="left", fill="x", expand=True)

        tk.Label(
            header_text,
            text="Attività e risultati",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")

        tk.Label(
            header_text,
            text="Qui trovi lo stato delle operazioni e i risultati delle ricerche.",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(3, 0))

        self.activity_status = tk.StringVar(value="Pronto")
        status_box = tk.Frame(
            card_header,
            bg="#eef0ff",
            highlightbackground="#dfe2ff",
            highlightthickness=1
        )
        status_box.pack(side="right", padx=(8, 12), pady=2)
        self.status_label = tk.Label(
            status_box,
            textvariable=self.activity_status,
            bg="#eef0ff",
            fg=ACCENT,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=5
        )
        self.status_label.pack()

        ttk.Button(
            card_header,
            text="Pulisci",
            command=self.clear_output
        ).pack(side="right", pady=2)

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=18)

        output_frame = tk.Frame(card, bg="#f7f8fc")
        output_frame.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=14
        )

        self.output = tk.Text(
            output_frame,
            bg="#f7f8fc",
            fg=TEXT,
            font=("Segoe UI", 10),
            wrap="word",
            relief="flat",
            borderwidth=0,
            padx=16,
            pady=14,
            spacing1=2,
            spacing3=5,
            selectbackground="#dfe2ff",
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
        self.output.bind("<MouseWheel>", self._scroll_output)
        self.output.bind("<Button-4>", self._scroll_output)
        self.output.bind("<Button-5>", self._scroll_output)

        self.output.tag_configure(
            "title",
            font=("Segoe UI", 14, "bold"),
            foreground=TEXT,
            spacing1=8,
            spacing3=8
        )

        self.output.tag_configure(
            "muted",
            foreground=MUTED,
            font=("Segoe UI", 9),
            spacing3=4
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
        self.output.tag_configure(
            "result_title",
            foreground=ACCENT,
            font=("Segoe UI", 11, "bold"),
            underline=True,
            spacing1=7,
            spacing3=1
        )
        self.output.tag_configure(
            "result_source",
            foreground=MUTED,
            font=("Segoe UI", 9),
            lmargin1=18,
            spacing3=7
        )

        # Barra di ricerca inferiore
        dock = tk.Frame(
            self.root,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        dock.grid(
            row=2, column=0, sticky="ew",
            padx=25, pady=(0, 20)
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

    def on_window_resize(self, event=None):
        """Adatta alcuni elementi alle dimensioni correnti della finestra."""
        if event is not None and event.widget is not self.root:
            return

        width = self.root.winfo_width()
        if width <= 1:
            return

        # La barra laterale si restringe gradualmente, senza bloccare il layout.
        if hasattr(self, "sidebar"):
            self.sidebar.configure(width=max(165, min(225, int(width * 0.21))))

        # Evita che il sottotitolo dell'intestazione si sovrapponga al selettore.
        if hasattr(self, "header_subtitle"):
            if width < 960:
                if self.header_subtitle.winfo_manager():
                    self.header_subtitle.pack_forget()
            elif not self.header_subtitle.winfo_manager():
                self.header_subtitle.pack(side="left", padx=12, pady=(10, 0))

    # =========================
    # SCORRIMENTO RISULTATI
    # =========================

    def _scroll_output(self, event):
        """Permette di scorrere i risultati con la rotellina del mouse."""
        if getattr(event, "num", None) == 4:
            self.output.yview_scroll(-3, "units")
        elif getattr(event, "num", None) == 5:
            self.output.yview_scroll(3, "units")
        else:
            delta = getattr(event, "delta", 0)
            if delta:
                self.output.yview_scroll(int(-delta / 120) * 3, "units")
        return "break"

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
        if hasattr(self, "activity_status"):
            self.activity_status.set("Pronto")

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
            "Esporta cronologia",
            "About"
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
            "Ricerca web": "Cerca pagine web con il motore selezionato.",
            "File per estensione": "Cerca file pubblicamente indicizzati.",
            "Analisi sito": "Cerca informazioni pubbliche su un dominio.",
            "Immagini": "Cerca immagini.",
            "Notizie": "Cerca notizie.",
            "Ricerca link": "Trova pagine e collegamenti correlati.",
            "Metadati": "Cerca pagine per titolo, URL e tipo di file.",
            "Cronologia": "Ricerche salvate localmente.",
            "Esporta cronologia": "Salva le ricerche in un file.",
            "About": "Informazioni su WebDesk."
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

        if mode == "About":
            self.clear_output()
            self.log("About", "title")
            self.log("Programmed by Daniel Secondi", "normal")
            self.log(f"Versione: {APP_VERSION}", "muted")
            return

        # Il cambio di funzione aggiorna solo titolo e descrizione:
        # non inserisce intestazioni testuali come "--- Notizie ---"
        # nell'area Attività e risultati.
        self.activity_status.set("Pronto")

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

    def make_url(self, query, kind="web", engine=None):

        encoded = quote_plus(query)
        engine = engine or self.engine.get()

        if kind == "images":
            if engine == "Bing":
                return "https://www.bing.com/images/search?q=" + encoded
            if engine == "DuckDuckGo":
                return "https://duckduckgo.com/?q=" + encoded + "&iax=images&ia=images"
            if engine == "Yahoo":
                return "https://images.search.yahoo.com/search/images?p=" + encoded
            return "https://www.google.com/search?tbm=isch&q=" + encoded

        if kind == "news":
            if engine == "Bing":
                return "https://www.bing.com/news/search?q=" + encoded
            if engine == "DuckDuckGo":
                return "https://duckduckgo.com/?q=" + encoded + "&iar=news&ia=news"
            if engine == "Yahoo":
                return "https://news.search.yahoo.com/search?p=" + encoded
            return "https://www.google.com/search?tbm=nws&q=" + encoded

        return ENGINES[engine] + encoded

    def _search_endpoint(self, query, engine_name, kind="web"):
        """Restituisce l'URL HTML da interrogare senza aprire il browser."""
        encoded = quote_plus(query)
        if engine_name == "Google":
            if kind == "images":
                return f"https://www.google.com/search?tbm=isch&q={encoded}"
            if kind == "news":
                return f"https://www.google.com/search?tbm=nws&q={encoded}"
            return f"https://www.google.com/search?q={encoded}"
        if engine_name == "Bing":
            if kind == "images":
                return f"https://www.bing.com/images/search?q={encoded}"
            if kind == "news":
                return f"https://www.bing.com/news/search?q={encoded}"
            return f"https://www.bing.com/search?q={encoded}"
        if engine_name == "DuckDuckGo":
            if kind == "images":
                return f"https://duckduckgo.com/?q={encoded}&iax=images&ia=images"
            if kind == "news":
                return f"https://duckduckgo.com/?q={encoded}&iar=news&ia=news"
            return f"https://html.duckduckgo.com/html/?q={encoded}"
        if engine_name == "Yahoo":
            if kind == "images":
                return f"https://images.search.yahoo.com/search/images?p={encoded}"
            if kind == "news":
                return f"https://news.search.yahoo.com/search?p={encoded}"
            return f"https://search.yahoo.com/search?p={encoded}"
        raise ValueError("Motore di ricerca non riconosciuto")

    def _extract_results(self, html, engine_name, base_url):
        """Estrae risultati HTML usando selettori specifici e controlli prudenti."""
        if BeautifulSoup is None:
            return []
        soup = BeautifulSoup(html, "html.parser")
        candidates = []
        selectors = {
            "Google": ["a:has(h3)", "div.MjjYud a:has(h3)", "a[href^='http']"],
            "Bing": ["li.b_algo h2 a", "h2 a", "a[href^='http']"],
            "DuckDuckGo": ["a.result__a", "a[data-testid='result-title-a']"],
            "Yahoo": ["h3 a", "a[href^='http']"]
        }
        blocked_hosts = (
            "google.com", "google.it", "bing.com", "duckduckgo.com",
            "yahoo.com", "search.yahoo.net", "microsoft.com"
        )
        for selector in selectors.get(engine_name, ["a[href^='http']"]):
            try:
                found = soup.select(selector)
            except Exception:
                found = []
            for anchor in found:
                href = anchor.get("href", "").strip()
                title = " ".join(anchor.get_text(" ", strip=True).split())
                if not href or not title or len(title) < 4:
                    continue
                if href.startswith("/url?"):
                    parsed_href = parse_url(href)
                    href = parse_qs(parsed_href.query).get("q", [""])[0]
                elif href.startswith("//"):
                    href = "https:" + href
                else:
                    href = urljoin(base_url, href)
                parsed = parse_url(href)
                if parsed.scheme not in ("http", "https") or not parsed.netloc:
                    continue
                host = parsed.netloc.lower().split(":")[0]
                if any(host == domain or host.endswith("." + domain) for domain in blocked_hosts):
                    continue
                if href.startswith(("javascript:", "mailto:")):
                    continue
                if any(existing["url"] == href for existing in candidates):
                    continue
                candidates.append({"title": title, "url": href, "source": engine_name})
                if len(candidates) >= 12:
                    return candidates
        return candidates

    def _extract_bing_rss(self, xml_text):
        """Legge il feed RSS di Bing: alternativa più stabile allo scraping HTML."""
        results = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return results
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            url = (item.findtext("link") or "").strip()
            if title and url.startswith(("http://", "https://")):
                if not any(row["url"] == url for row in results):
                    results.append({"title": title, "url": url, "source": "Bing RSS"})
            if len(results) >= 12:
                break
        return results

    def _fetch_engine(self, query, engine_name, kind):
        if requests is None:
            raise RuntimeError("Manca requests. Installa le librerie con: py -m pip install requests beautifulsoup4")

        url = self._search_endpoint(query, engine_name, kind)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        errors = []
        results = []
        try:
            response = requests.get(url, headers=headers, timeout=(6, 12), allow_redirects=True)
            response.raise_for_status()
            results = self._extract_results(response.text, engine_name, response.url)
        except Exception as exc:
            errors.append(str(exc))

        # Se il motore blocca lo scraping HTML, per la ricerca web usa il feed RSS
        # pubblico di Bing come recupero. Non viene usato per immagini o notizie.
        if not results and kind == "web":
            try:
                rss_url = "https://www.bing.com/search?format=rss&q=" + quote_plus(query)
                rss_response = requests.get(rss_url, headers=headers, timeout=(6, 12))
                rss_response.raise_for_status()
                results = self._extract_bing_rss(rss_response.text)
            except Exception as exc:
                errors.append("recupero RSS: " + str(exc))

        if not results and errors:
            raise RuntimeError("; ".join(errors))
        return engine_name, results

    def _show_search_results(self, query, results_by_engine, errors):
        self.log(f"Risultati per: {query}", "title")
        total = 0
        for engine_name in results_by_engine:
            results = results_by_engine[engine_name]
            self.log(f"\n{engine_name} — {len(results)} risultati", "success")
            if not results:
                self.log("Nessun risultato disponibile. Prova un altro motore o ripeti la ricerca.", "muted")
                continue
            for index, item in enumerate(results, 1):
                self.output.configure(state="normal")
                tag = f"result_{total}_{index}"
                self.output.insert("end", f"{index}. {item['title']}\n", ("result_title", tag))
                self.output.tag_bind(tag, "<Button-1>", lambda event, url=item["url"]: webbrowser.open_new_tab(url))
                self.output.insert("end", item["url"] + "\n", "result_source")
                if item.get("source") == "Bing RSS" and engine_name != "Bing":
                    self.output.insert("end", "Fonte: Bing (risultati di riserva)\n", "muted")
                self.output.insert("end", "\n", "result_source")
                self.output.configure(state="disabled")
                total += 1
        for engine_name, error in errors.items():
            self.log(f"{engine_name}: {error}", "muted")
        self.log(f"Totale: {total} risultati trovati. Clicca un titolo per aprire la pagina.", "success")
        if hasattr(self, "activity_status"):
            self.activity_status.set(f"{total} risultati")
        self.save_history()

    def open_search_all(self, query, kind="web"):
        self.open_search(query, kind)

    def open_search(self, query, kind="web"):
        """Cerca nell'app e mostra i titoli; non apre automaticamente il browser."""
        selected = list(ENGINES.keys()) if self.engine.get() == "Tutti i motori" else [self.engine.get()]
        self.activity_status.set("Ricerca in corso…")
        self.log(f"Ricerca in corso su: {', '.join(selected)}...", "muted")
        self.search_entry.configure(state="disabled")

        def worker():
            results_by_engine = {}
            errors = {}
            # Esecuzione in parallelo: i motori non si bloccano a vicenda.
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected)) as executor:
                futures = {executor.submit(self._fetch_engine, query, name, kind): name for name in selected}
                for future in concurrent.futures.as_completed(futures):
                    name = futures[future]
                    try:
                        engine_name, results = future.result()
                        results_by_engine[engine_name] = results
                    except Exception as error:
                        errors[name] = str(error)
            ordered = {name: results_by_engine.get(name, []) for name in selected if name in results_by_engine}
            self.root.after(0, lambda: self._finish_search(query, ordered, errors, selected))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_search(self, query, results_by_engine, errors, selected):
        self.search_entry.configure(state="normal")
        for engine_name in selected:
            # La cronologia conserva un record per ogni motore interrogato.
            url = self._search_endpoint(query, engine_name)
            self.history.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mode": self.mode,
                "engine": engine_name,
                "query": query,
                "url": url
            })
        self._show_search_results(query, results_by_engine, errors)

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

        self.log(
            f"Sito da analizzare: {candidate}",
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

        if self.mode == "About":
            return

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