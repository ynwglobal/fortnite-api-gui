import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import requests
import json
import time
import os
from Crypto.Cipher import AES
import base64

CACHE_FILE = "fnapi_cache.json"
HISTORY_FILE = "fnapi_history.json"
CONFIG_FILE = "fnapi_config.json"

RATE_LIMIT_SECONDS = 1.5  # Delay between API calls to avoid spam


class FortniteAPI:
    BASE_URL = "https://fortnite-api.com"

    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Authorization": api_key})
        self.cache = self.load_cache()
        self.last_call_time = 0

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                return json.load(open(CACHE_FILE, "r", encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save_cache(self):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def rate_limit(self):
        elapsed = time.time() - self.last_call_time
        if elapsed < RATE_LIMIT_SECONDS:
            time.sleep(RATE_LIMIT_SECONDS - elapsed)
        self.last_call_time = time.time()

    def get(self, path, params=None):
        key = f"{path} {params}"
        if key in self.cache:
            return self.cache[key]
        self.rate_limit()
        url = f"{self.BASE_URL}{path}"
        try:
            r = self.session.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            self.cache[key] = data
            self.save_cache()
            return data
        except Exception as e:
            return {"error": str(e)}

    def get_cosmetics(self, search=""):
        return self.get("/v2/cosmetics/br/search/all", params={"name": search} if search else None)

    def get_news(self):
        return self.get("/v2/news/br")

    def get_stats(self, epic_username):
        return self.get(f"/v2/stats/br/v2", params={"name": epic_username})

    def get_shop(self):
        return self.get("/v2/shop/br")

    def get_map(self):
        return self.get("/v1/map")

    def get_season(self):
        return self.get("/v2/seasons/current")

    def get_languages(self):
        return self.get("/v1/languages")

    def get_upcoming(self):
        return self.get("/v2/cosmetics/br/new")

    def get_creative(self):
        return self.get("/v2/creative/islands")

    def get_paks(self):
        return self.get("/v2/paks")

    def get_banners(self):
        return self.get("/v1/banners")

    def get_creator_code(self, creator_code):
        return self.get(f"/v2/creatorcode/{creator_code}")


class FortniteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("fortnite-api.com")
        self.api_key = ""
        self.api = None
        self.history = self.load_history()
        self.load_config()

        self.create_widgets()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.api_key = cfg.get("api_key", "")
                    if self.api_key:
                        self.api = FortniteAPI(self.api_key)
            except Exception:
                pass

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"api_key": self.api_key}, f, indent=2)

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                return json.load(open(HISTORY_FILE, "r", encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save_history(self):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    def add_history(self, category, entry):
        if category not in self.history:
            self.history[category] = []
        self.history[category].append({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "entry": entry})
        # Limit to last 25
        if len(self.history[category]) > 25:
            self.history[category] = self.history[category][-25:]
        self.save_history()

    def create_widgets(self):
        # Create Credits button on top right
        credits_btn = ttk.Button(self.root, text="Credits", command=self.show_credits)
        credits_btn.pack(anchor="ne", padx=10, pady=5)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Create all tabs
        self.tabs = {}

        tab_names = [
            "Cosmetics", "News", "Stats", "Shop", "Map Info", "Season Info",
            "Languages", "Upcoming", "Creative", "Paks", "Banners",
            "AES Decrypt", "Creator Codes", "Settings"
        ]

        for name in tab_names:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=name)
            self.tabs[name] = frame

        self.build_cosmetics_tab()
        self.build_news_tab()
        self.build_stats_tab()
        self.build_shop_tab()
        self.build_map_tab()
        self.build_season_tab()
        self.build_languages_tab()
        self.build_upcoming_tab()
        self.build_creative_tab()
        self.build_paks_tab()
        self.build_banners_tab()
        self.build_aes_tab()
        self.build_creator_code_tab()
        self.build_settings_tab()

        self.status_label = ttk.Label(self.root, text="Welcome to fortnite-api.com", relief=tk.SUNKEN, anchor="w")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def show_credits(self):
        messagebox.showinfo("Credits", "Created by:\n\nhbkvxncent\nynwglobal")

    def set_status(self, text):
        self.status_label.config(text=text)

    # --- Build individual tabs ---

    def build_cosmetics_tab(self):
        tab = self.tabs["Cosmetics"]
        ttk.Label(tab, text="Search Cosmetics by Name:").pack(anchor="w", padx=5, pady=5)
        self.cos_search_var = tk.StringVar()
        search_entry = ttk.Entry(tab, textvariable=self.cos_search_var)
        search_entry.pack(fill="x", padx=5)
        search_entry.bind("<Return>", lambda e: self.threaded(self.do_cosmetics_search)())

        search_btn = ttk.Button(tab, text="Search", command=self.threaded(self.do_cosmetics_search))
        search_btn.pack(pady=5)

        self.cos_results = scrolledtext.ScrolledText(tab, height=15, wrap=tk.WORD)
        self.cos_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_cosmetics_search(self):
        query = self.cos_search_var.get().strip()
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        if not query:
            messagebox.showinfo("Input Required", "Please enter a cosmetic name to search.")
            return

        self.set_status(f"Searching cosmetics for '{query}'...")
        data = self.api.get_cosmetics(query)
        self.set_status("Search complete.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        items = data.get("data", [])
        output = []
        for item in items:
            output.append(f"Name: {item.get('name')}")
            output.append(f"Type: {item.get('type', {}).get('value')}")
            output.append(f"Rarity: {item.get('rarity', {}).get('value')}")
            output.append(f"ID: {item.get('id')}")
            output.append("-" * 40)

        self.cos_results.delete(1.0, tk.END)
        self.cos_results.insert(tk.END, "\n".join(output))
        self.add_history("cosmetics", query)

    def build_news_tab(self):
        tab = self.tabs["News"]
        refresh_btn = ttk.Button(tab, text="Refresh News", command=self.threaded(self.do_news_refresh))
        refresh_btn.pack(pady=5)
        self.news_results = scrolledtext.ScrolledText(tab, height=20, wrap=tk.WORD)
        self.news_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_news_refresh(self):
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        self.set_status("Fetching news...")
        data = self.api.get_news()
        self.set_status("News fetched.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        news_items = data.get("data", {}).get("br", {}).get("motds", [])
        output = []
        for n in news_items:
            output.append(f"Title: {n.get('title')}")
            output.append(f"Body: {n.get('body')}")
            output.append("-" * 40)

        self.news_results.delete(1.0, tk.END)
        self.news_results.insert(tk.END, "\n".join(output))
        self.add_history("news", "refresh")

    def build_stats_tab(self):
        tab = self.tabs["Stats"]
        ttk.Label(tab, text="Enter Epic Username:").pack(anchor="w", padx=5, pady=5)
        self.stats_user_var = tk.StringVar()
        user_entry = ttk.Entry(tab, textvariable=self.stats_user_var)
        user_entry.pack(fill="x", padx=5)
        user_entry.bind("<Return>", lambda e: self.threaded(self.do_stats_lookup)())

        stats_btn = ttk.Button(tab, text="Lookup Stats", command=self.threaded(self.do_stats_lookup))
        stats_btn.pack(pady=5)

        self.stats_results = scrolledtext.ScrolledText(tab, height=25, wrap=tk.WORD)
        self.stats_results.pack(expand=True, fill="both", padx=5, pady=5)

    def format_stat_category(self, category_name, stats_dict):
        # Format each category (Overall, Solo, Duo, Squad, LTM) neat and readable
        lines = [f"=== {category_name} Stats ==="]
        # Select keys and display in neat order with friendly names and formatting
        keys_order = [
            ("score", "Score"),
            ("scorePerMin", "Score Per Minute"),
            ("scorePerMatch", "Score Per Match"),
            ("wins", "Wins"),
            ("top3", "Top 3 Finishes"),
            ("top5", "Top 5 Finishes"),
            ("top6", "Top 6 Finishes"),
            ("top10", "Top 10 Finishes"),
            ("top12", "Top 12 Finishes"),
            ("top25", "Top 25 Finishes"),
            ("kills", "Kills"),
            ("killsPerMin", "Kills Per Minute"),
            ("killsPerMatch", "Kills Per Match"),
            ("deaths", "Deaths"),
            ("kd", "K/D Ratio"),
            ("matches", "Matches Played"),
            ("winRate", "Win Rate (%)"),
            ("minutesPlayed", "Minutes Played"),
            ("playersOutlived", "Players Outlived"),
            ("lastModified", "Last Modified"),
        ]

        for key, label in keys_order:
            if key in stats_dict:
                value = stats_dict[key]
                # Format floats nicely
                if isinstance(value, float):
                    value = f"{value:.3f}"
                lines.append(f"{label}: {value}")
        lines.append("")  # blank line for spacing
        return "\n".join(lines)

    def do_stats_lookup(self):
        username = self.stats_user_var.get().strip()
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        if not username:
            messagebox.showinfo("Input Required", "Please enter an Epic username.")
            return

        self.set_status(f"Fetching stats for {username}...")
        data = self.api.get_stats(username)
        self.set_status("Stats fetched.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        stats_data = data.get("data", {}).get("stats", {}).get("all", {})

        # Categories to format: Overall, Solo, Duo, Squad, Ltm
        output_sections = []
        for cat in ["overall", "solo", "duo", "squad", "ltm"]:
            cat_stats = stats_data.get(cat, {})
            if cat_stats:
                name = cat.capitalize()
                section_text = self.format_stat_category(name, cat_stats)
                output_sections.append(section_text)

        if not output_sections:
            self.stats_results.delete(1.0, tk.END)
            self.stats_results.insert(tk.END, "No stats available for this user.")
        else:
            self.stats_results.delete(1.0, tk.END)
            self.stats_results.insert(tk.END, "\n".join(output_sections))

        self.add_history("stats", username)

    def build_shop_tab(self):
        tab = self.tabs["Shop"]
        refresh_btn = ttk.Button(tab, text="Refresh Shop", command=self.threaded(self.do_shop_refresh))
        refresh_btn.pack(pady=5)
        self.shop_results = scrolledtext.ScrolledText(tab, height=20, wrap=tk.WORD)
        self.shop_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_shop_refresh(self):
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return

        self.set_status("Fetching shop data...")
        data = self.api.get_shop()
        self.set_status("Shop data fetched.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        items = data.get("data", {}).get("featured", []) + data.get("data", {}).get("daily", [])
        output = []
        for item in items:
            output.append(f"{item.get('name')} - Price: {item.get('price')} V-Bucks - Rarity: {item.get('rarity', {}).get('value')}")
            output.append("-" * 40)

        self.shop_results.delete(1.0, tk.END)
        self.shop_results.insert(tk.END, "\n".join(output))
        self.add_history("shop", "refresh")

    def build_map_tab(self):
        tab = self.tabs["Map Info"]
        refresh_btn = ttk.Button(tab, text="Refresh Map Info", command=self.threaded(self.do_map_info))
        refresh_btn.pack(pady=5)
        self.map_results = scrolledtext.ScrolledText(tab, height=20, wrap=tk.WORD)
        self.map_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_map_info(self):
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        self.set_status("Fetching map info...")
        data = self.api.get_map()
        self.set_status("Map info fetched.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        pois = data.get("data", {}).get("pois", [])
        output = []
        for p in pois:
            coords = p.get("coordinates", "")
            output.append(f"{p.get('name')} - Coordinates: {coords}")
        self.map_results.delete(1.0, tk.END)
        self.map_results.insert(tk.END, "\n".join(output))

    def build_season_tab(self):
        tab = self.tabs["Season Info"]
        refresh_btn = ttk.Button(tab, text="Refresh Season Info", command=self.threaded(self.do_season_info))
        refresh_btn.pack(pady=5)
        self.season_results = scrolledtext.ScrolledText(tab, height=10, wrap=tk.WORD)
        self.season_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_season_info(self):
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        self.set_status("Fetching season info...")
        data = self.api.get_season()
        self.set_status("Season info fetched.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        d = data.get("data", {})
        text = (
            f"Chapter: {d.get('chapter')}\n"
            f"Season: {d.get('season')}\n"
            f"Start Date: {d.get('startDate')}\n"
            f"End Date: {d.get('endDate')}"
        )
        self.season_results.delete(1.0, tk.END)
        self.season_results.insert(tk.END, text)

    def build_languages_tab(self):
        tab = self.tabs["Languages"]
        refresh_btn = ttk.Button(tab, text="Refresh Languages", command=self.threaded(self.do_languages_list))
        refresh_btn.pack(pady=5)
        self.lang_results = scrolledtext.ScrolledText(tab, height=15, wrap=tk.WORD)
        self.lang_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_languages_list(self):
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        self.set_status("Fetching languages...")
        data = self.api.get_languages()
        self.set_status("Languages fetched.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        languages = data.get("data", [])
        output = [f"{l.get('code')}: {l.get('name')}" for l in languages]
        self.lang_results.delete(1.0, tk.END)
        self.lang_results.insert(tk.END, "\n".join(output))

    def build_upcoming_tab(self):
        tab = self.tabs["Upcoming"]
        refresh_btn = ttk.Button(tab, text="Refresh Upcoming Cosmetics", command=self.threaded(self.do_upcoming))
        refresh_btn.pack(pady=5)
        self.upcoming_results = scrolledtext.ScrolledText(tab, height=20, wrap=tk.WORD)
        self.upcoming_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_upcoming(self):
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        self.set_status("Fetching upcoming cosmetics...")
        data = self.api.get_upcoming()
        self.set_status("Upcoming cosmetics fetched.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        items = data.get("data", [])
        output = []
        for item in items:
            output.append(f"{item.get('name')} ({item.get('type', {}).get('value')})")
            output.append("-" * 40)

        self.upcoming_results.delete(1.0, tk.END)
        self.upcoming_results.insert(tk.END, "\n".join(output))

    def build_creative_tab(self):
        tab = self.tabs["Creative"]
        refresh_btn = ttk.Button(tab, text="Refresh Creative Islands", command=self.threaded(self.do_creative))
        refresh_btn.pack(pady=5)
        self.creative_results = scrolledtext.ScrolledText(tab, height=20, wrap=tk.WORD)
        self.creative_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_creative(self):
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        self.set_status("Fetching creative islands...")
        data = self.api.get_creative()
        self.set_status("Creative islands fetched.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        islands = data.get("data", [])
        output = []
        for island in islands:
            output.append(f"{island.get('title')} by {island.get('creatorName')}")
            output.append(f"Code: {island.get('code')}")
            output.append("-" * 40)

        self.creative_results.delete(1.0, tk.END)
        self.creative_results.insert(tk.END, "\n".join(output))

    def build_paks_tab(self):
        tab = self.tabs["Paks"]
        refresh_btn = ttk.Button(tab, text="Refresh Paks Info", command=self.threaded(self.do_paks))
        refresh_btn.pack(pady=5)
        self.paks_results = scrolledtext.ScrolledText(tab, height=20, wrap=tk.WORD)
        self.paks_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_paks(self):
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        self.set_status("Fetching paks info...")
        data = self.api.get_paks()
        self.set_status("Paks info fetched.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        paks = data.get("data", [])
        output = []
        for pak in paks:
            output.append(f"Name: {pak.get('name')}")
            output.append(f"Path: {pak.get('path')}")
            output.append("-" * 40)

        self.paks_results.delete(1.0, tk.END)
        self.paks_results.insert(tk.END, "\n".join(output))

    def build_banners_tab(self):
        tab = self.tabs["Banners"]
        refresh_btn = ttk.Button(tab, text="Refresh Banners", command=self.threaded(self.do_banners))
        refresh_btn.pack(pady=5)
        self.banners_results = scrolledtext.ScrolledText(tab, height=20, wrap=tk.WORD)
        self.banners_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_banners(self):
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        self.set_status("Fetching banners...")
        data = self.api.get_banners()
        self.set_status("Banners fetched.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        banners = data.get("data", [])
        output = []
        for b in banners:
            output.append(f"Name: {b.get('name')}")
            output.append(f"Category: {b.get('category')}")
            output.append("-" * 40)

        self.banners_results.delete(1.0, tk.END)
        self.banners_results.insert(tk.END, "\n".join(output))

    def build_aes_tab(self):
        tab = self.tabs["AES Decrypt"]
        ttk.Label(tab, text="Enter Base64 Encrypted Text:").pack(anchor="w", padx=5, pady=5)
        self.aes_input = tk.Text(tab, height=5)
        self.aes_input.pack(fill="x", padx=5)

        ttk.Label(tab, text="Enter Key (16, 24 or 32 chars):").pack(anchor="w", padx=5, pady=5)
        self.aes_key_var = tk.StringVar()
        aes_key_entry = ttk.Entry(tab, textvariable=self.aes_key_var, show="*")
        aes_key_entry.pack(fill="x", padx=5)

        decrypt_btn = ttk.Button(tab, text="Decrypt", command=self.do_aes_decrypt)
        decrypt_btn.pack(pady=5)

        ttk.Label(tab, text="Decrypted Text:").pack(anchor="w", padx=5, pady=5)
        self.aes_output = scrolledtext.ScrolledText(tab, height=10, wrap=tk.WORD)
        self.aes_output.pack(expand=True, fill="both", padx=5, pady=5)

    def do_aes_decrypt(self):
        enc_text = self.aes_input.get("1.0", "end").strip()
        key = self.aes_key_var.get()
        if not enc_text or not key:
            messagebox.showerror("Input Error", "Both encrypted text and key are required.")
            return

        try:
            raw = base64.b64decode(enc_text)
            cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
            decrypted = cipher.decrypt(raw)
            # Remove PKCS7 padding
            pad_len = decrypted[-1]
            decrypted = decrypted[:-pad_len]
            self.aes_output.delete(1.0, tk.END)
            self.aes_output.insert(tk.END, decrypted.decode("utf-8"))
        except Exception as e:
            messagebox.showerror("Decryption Error", str(e))

    def build_creator_code_tab(self):
        tab = self.tabs["Creator Codes"]
        ttk.Label(tab, text="Enter Creator Code:").pack(anchor="w", padx=5, pady=5)
        self.creator_code_var = tk.StringVar()
        creator_code_entry = ttk.Entry(tab, textvariable=self.creator_code_var)
        creator_code_entry.pack(fill="x", padx=5)
        creator_code_entry.bind("<Return>", lambda e: self.threaded(self.do_creator_code_lookup)())

        lookup_btn = ttk.Button(tab, text="Lookup", command=self.threaded(self.do_creator_code_lookup))
        lookup_btn.pack(pady=5)

        self.creator_code_results = scrolledtext.ScrolledText(tab, height=15, wrap=tk.WORD)
        self.creator_code_results.pack(expand=True, fill="both", padx=5, pady=5)

    def do_creator_code_lookup(self):
        code = self.creator_code_var.get().strip()
        if not self.api:
            messagebox.showerror("API Key Missing", "Please enter a valid API key in Settings.")
            return
        if not code:
            messagebox.showinfo("Input Required", "Please enter a creator code.")
            return

        self.set_status(f"Looking up creator code '{code}'...")
        data = self.api.get_creator_code(code)
        self.set_status("Lookup complete.")
        if "error" in data:
            messagebox.showerror("API Error", data["error"])
            return

        d = data.get("data", {})
        output = [
            f"Creator: {d.get('account', {}).get('name')}",
            f"Share Code: {d.get('account', {}).get('shareCode')}",
            f"Platform: {d.get('account', {}).get('platform')}",
            f"Total Payments: {d.get('payments', 0)}",
        ]
        self.creator_code_results.delete(1.0, tk.END)
        self.creator_code_results.insert(tk.END, "\n".join(output))

    def build_settings_tab(self):
        tab = self.tabs["Settings"]
        ttk.Label(tab, text="Enter Your Fortnite API Key:").pack(anchor="w", padx=5, pady=5)
        self.api_key_var = tk.StringVar(value=self.api_key)
        api_entry = ttk.Entry(tab, textvariable=self.api_key_var, show="*")
        api_entry.pack(fill="x", padx=5)

        save_btn = ttk.Button(tab, text="Save API Key", command=self.save_api_key)
        save_btn.pack(pady=5)

    def save_api_key(self):
        key = self.api_key_var.get().strip()
        if not key:
            messagebox.showerror("Input Error", "API Key cannot be empty.")
            return
        self.api_key = key
        self.api = FortniteAPI(self.api_key)
        self.save_config()
        messagebox.showinfo("Saved", "API Key saved successfully.")
        self.set_status("API Key updated.")

    # Utility for threading API calls to avoid freezing GUI
    def threaded(self, func):
        def wrapper(*args, **kwargs):
            threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()
        return wrapper


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x700")
    app = FortniteApp(root)
    root.mainloop()
