import time
import json
import sqlite3
import pandas as pd
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import tkinter as tk
from tkinter import ttk
from threading import Thread
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class InteractiveScraper:
    def __init__(self, headless=False, use_proxy=False, proxy=None):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        if use_proxy and proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

    def load_page(self, url):
        self.driver.get(url)
        time.sleep(2)

    def handle_cookie_banner(self):
        try:
            accept_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
            if accept_button:
                accept_button.click()
                print("Cookie banner accepted.")
        except NoSuchElementException:
            print("No cookie banner found.")

    def handle_captcha(self):
        input("CAPTCHA detected. Please solve the CAPTCHA in the browser window and press Enter to continue...")

    def inject_selection_script(self):
        js = """
        if (!window.__selectedElement) {
            window.__selectedElement = null;
            function highlightElement(e) {
                e.target.style.outline = '2px solid red';
            }
            function unhighlightElement(e) {
                e.target.style.outline = '';
            }
            document.addEventListener('mouseover', highlightElement, false);
            document.addEventListener('mouseout', unhighlightElement, false);
            document.addEventListener('click', function(e){
                e.preventDefault();
                e.stopPropagation();
                window.__selectedElement = {
                    tag: e.target.tagName,
                    id: e.target.id,
                    classes: e.target.className,
                    text: e.target.innerText
                };
                alert("Element selected: " + window.__selectedElement.tag);
            }, {once: true});
        }
        """
        self.driver.execute_script(js)

    def wait_for_selection(self, timeout=60):
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.driver.execute_script("return window.__selectedElement;")
            if result:
                return result
            time.sleep(0.5)
        return None

    def compute_selector(self, element_info):
        if element_info.get("id"):
            return f"#{element_info['id']}"
        selector = element_info["tag"].lower()
        if element_info.get("classes"):
            classes = element_info["classes"].split()
            for cls in classes:
                selector += f".{cls}"
        return selector

    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def parse_element(self, element):
        soup = BeautifulSoup(element.get_attribute('outerHTML'), 'html.parser')
        text = soup.get_text()
        cleaned_text = self.clean_text(text)
        return cleaned_text

    def extract_similar_elements(self, selector):
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            data = []
            for el in elements:
                parsed_data = {
                    "tag": el.tag_name,
                    "text": self.parse_element(el),
                    "html": el.get_attribute('outerHTML')
                }
                data.append(parsed_data)
            return data
        except Exception as e:
            print("Error extracting elements:", e)
            return []

    # Export functions
    def export_to_csv(self, data, filename):
        pd.DataFrame(data).to_csv(filename, index=False)

    def export_to_json(self, data, filename):
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    def export_to_xlsx(self, data, filename):
        pd.DataFrame(data).to_excel(filename, index=False)

    def export_to_sqlite(self, data, filename):
        conn = sqlite3.connect(filename)
        pd.DataFrame(data).to_sql("data", conn, if_exists="replace", index=False)
        conn.close()

    def quit(self):
        self.driver.quit()

def start_scraper(url, headless, max_pages, use_proxy, proxy):
    scraper = InteractiveScraper(headless=headless, use_proxy=use_proxy, proxy=proxy)
    scraper.load_page(url)
    scraper.handle_cookie_banner()
    
    if not headless:
        print("Injecting selection script. Please hover over and click the element you wish to select.")
        scraper.inject_selection_script()
        
        element_info = scraper.wait_for_selection()
        if not element_info:
            print("No element selected within the time limit. Exiting.")
            scraper.quit()
            return
        
        print("Element selected:", element_info)
        selector = scraper.compute_selector(element_info)
        print("Computed CSS selector for similar elements:", selector)
        
        data = scraper.extract_similar_elements(selector)
        print(f"Found {len(data)} elements matching the selector.")
        
        scraper.export_to_csv(data, "extracted_data.csv")
        print("Data exported to extracted_data.csv")
    
    scraper.quit()

def on_start():
    url = url_entry.get()
    max_pages = int(max_pages_entry.get())
    headless = headless_var.get()
    use_proxy = use_proxy_var.get()
    proxy = proxy_entry.get()
    scraper_thread = Thread(target=start_scraper, args=(url, headless, max_pages, use_proxy, proxy))
    scraper_thread.start()

# Create the main window
root = tk.Tk()
root.title("Web Scraper")

# URL Entry
url_label = ttk.Label(root, text="URL:")
url_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
url_entry = ttk.Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=5, pady=5)

# Max Pages Entry
max_pages_label = ttk.Label(root, text="Max Pages:")
max_pages_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
max_pages_entry = ttk.Entry(root, width=10)
max_pages_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

# Headless Mode Checkbox
headless_var = tk.BooleanVar()
headless_checkbox = ttk.Checkbutton(root, text="Run in Headless Mode", variable=headless_var)
headless_checkbox.grid(row=2, column=0, columnspan=2, pady=5)

# Proxy Support
use_proxy_var = tk.BooleanVar()
use_proxy_checkbox = ttk.Checkbutton(root, text="Use Proxy", variable=use_proxy_var)
use_proxy_checkbox.grid(row=3, column=0, columnspan=2, pady=5)

proxy_label = ttk.Label(root, text="Proxy:")
proxy_label.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
proxy_entry = ttk.Entry(root, width=50)
proxy_entry.grid(row=4, column=1, padx=5, pady=5)

# Start Button
start_button = ttk.Button(root, text="Start Scraper", command=on_start)
start_button.grid(row=5, column=0, columnspan=2, pady=10)

# Data Visualization Section
def visualize_data():
    try:
        data = pd.read_csv("extracted_data.csv")
        fig, ax = plt.subplots()
        data['text'].value_counts().plot(kind='bar', ax=ax)
        ax.set_title('Frequency of Extracted Text')
        ax.set_xlabel('Text')
        ax.set_ylabel('Frequency')
        
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.draw()
        canvas.get_tk_widget().grid(row=6, column=0, columnspan=2, pady=10)
    except Exception as e:
        print("Error visualizing data:", e)

visualize_button = ttk.Button(root, text="Visualize Data", command=visualize_data)
visualize_button.grid(row=6, column=0, columnspan=2, pady=10)

# Run the application
root.mainloop()
