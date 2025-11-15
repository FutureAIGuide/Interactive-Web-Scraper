# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Set environment variables for headless operation
ENV URL_TO_SCRAPE="http://quotes.toscrape.com"
ENV MAX_PAGES=1
ENV HEADLESS=True
ENV USE_PROXY=False
ENV PROXY=""

# Modify the script to be executable and use environment variables
RUN sed -i '1i#!/usr/bin/env python' enhanced_interactive_scraper.py && \
    sed -i "/root = tk.Tk()/i \
import os\n\
if os.getenv('HEADLESS') == 'True':\n\
    url = os.getenv('URL_TO_SCRAPE', 'http://example.com')\n\
    max_pages = int(os.getenv('MAX_PAGES', 1))\n\
    headless = True\n\
    use_proxy = os.getenv('USE_PROXY', 'False').lower() in ('true', '1', 't')\n\
    proxy = os.getenv('PROXY', '')\n\
    start_scraper(url, headless, max_pages, use_proxy, proxy)\n\
else:" enhanced_interactive_scraper.py

# Run the application
CMD ["python", "enhanced_interactive_scraper.py"]