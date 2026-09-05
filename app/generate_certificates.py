#!/usr/bin/env python3
"""
Certificate Generator Automation Script
--------------------------------------
This script automates putting names from a CSV file onto a PDF certificate template.
It reads settings like font size, font URL, and top offset position from a config.json file.
It produces individual PDFs and outputs a certificate log CSV file indicating which
name was applied to which PDF file.
"""

import os
import sys
import csv
import re
import io
import json
import requests
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Resolve absolute paths relative to the location of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

# Default settings
DEFAULT_CONFIG = {
    "font_size": 16.50,
    "top_offset_ratio": 0.40,
    "font_name": "Montserrat-Medium",
    "font_filename": "Montserrat-Medium.ttf",
    "font_url": "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Medium.ttf",
    "text_color_rgb": [0.15, 0.15, 0.15],
    "max_text_width_ratio": 0.80
}


def load_config():
    """Load config.json file. Falls back to DEFAULT_CONFIG if loading fails."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            print(f"[Config] Loaded settings from: {CONFIG_PATH}")
            return merged
        except Exception as e:
            print(f"[Config] WARNING: Failed to load config.json: {e}. Using defaults.")
    else:
        # Save default config.json
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            print(f"[Config] Created default settings file at: {CONFIG_PATH}")
        except Exception as e:
            print(f"[Config] WARNING: Failed to save config.json: {e}")
    return DEFAULT_CONFIG


# Load Config
CONFIG = load_config()

FONT_URL = CONFIG["font_url"]
FONT_NAME = CONFIG["font_name"]
FONT_FILENAME = CONFIG["font_filename"]

TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "src", "docker-certificate.pdf")
NAMES_CSV_PATH = os.path.join(PROJECT_ROOT, "src", "names.csv")
OUT_DIR = os.path.join(PROJECT_ROOT, "out")
LOG_CSV_PATH = os.path.join(OUT_DIR, "names_applied_log.csv")
FONT_PATH = os.path.join(SCRIPT_DIR, FONT_FILENAME)


def sanitize_filename(name):
    r"""
    Sanitize names to be safe for filenames on Windows, macOS, and Linux.
    Removes characters like \ / : * ? " < > |
    """
    # Replace illegal characters with empty space
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    # Strip leading/trailing spaces and dots
    return cleaned.strip().strip('.')


def ensure_font():
    """
    Ensure Montserrat-Medium.ttf is available in the app directory.
    If not, it checks the src folder, then falls back to downloading it from Google Fonts repository.
    """
    if os.path.exists(FONT_PATH):
        print(f"[Font] Found local font at: {FONT_PATH}")
        return

    # Check src folder
    src_font_path = os.path.join(PROJECT_ROOT, "src", FONT_FILENAME)
    if os.path.exists(src_font_path):
        print(f"[Font] Found font file in src/ directory, copying to: {FONT_PATH}")
        import shutil
        shutil.copy(src_font_path, FONT_PATH)
        return

    print(f"[Font] Font not found locally. Downloading '{FONT_NAME}' from Google Fonts GitHub...")
    try:
        response = requests.get(FONT_URL, timeout=30)
        response.raise_for_status()
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)
        print(f"[Font] Font downloaded successfully and saved to: {FONT_PATH}")
    except Exception as e:
        print(f"[Font] WARNING: Failed to download font: {e}")
        print("[Font] Helvetica standard font will be used as a fallback.")


def create_text_overlay(name, width, height, font_name):
    """
    Generate an in-memory PDF overlay page with the recipient's name
    centered horizontally and positioned vertically based on config.
    """
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))

    # Base font size and constraint configurations from CONFIG
    base_font_size = CONFIG["font_size"]
    max_text_width = width * CONFIG["max_text_width_ratio"]
    current_font_size = base_font_size

    # Clean name
    name_str = name.strip()

    # Dynamic scaling for long names
    try:
        text_width = pdfmetrics.stringWidth(name_str, font_name, current_font_size)
        if text_width > max_text_width:
            current_font_size = current_font_size * (max_text_width / text_width)
            current_font_size = max(current_font_size, 10.0)  # Prevent font from shrinking too much
            print(f"  [Style] Scaling font size to {current_font_size:.2f}pt for long name: '{name_str}'")
    except Exception as e:
        print(f"  [Style] Could not calculate string width: {e}. Using default size.")

    can.setFont(font_name, current_font_size)

    # Positions:
    # Centered horizontally
    x = width / 2.0
    # From top is top_offset_ratio of height. ReportLab canvas Y starts from bottom.
    # Therefore, from bottom is: height * (1 - top_offset_ratio)
    y = height * (1.0 - CONFIG["top_offset_ratio"])

    # Draw centered string with clean configured color
    color_rgb = CONFIG["text_color_rgb"]
    can.setFillColorRGB(color_rgb[0], color_rgb[1], color_rgb[2])
    can.drawCentredString(x, y, name_str)
    can.save()

    packet.seek(0)
    return packet


def process_certificates():
    # Make sure output directory exists
    os.makedirs(OUT_DIR, exist_ok=True)

    # Verify input template exists
    if not os.path.exists(TEMPLATE_PATH):
        print(f"[Error] Certificate template not found at: {TEMPLATE_PATH}")
        sys.exit(1)

    # Verify input CSV exists
    if not os.path.exists(NAMES_CSV_PATH):
        print(f"[Error] Names CSV not found at: {NAMES_CSV_PATH}")
        sys.exit(1)

    # Font setup
    ensure_font()
    registered_font = "Helvetica"
    if os.path.exists(FONT_PATH):
        try:
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
            registered_font = FONT_NAME
            print(f"[Font] Successfully registered '{FONT_NAME}' for ReportLab canvas.")
        except Exception as e:
            print(f"[Font] Error registering '{FONT_NAME}': {e}. Falling back to Helvetica.")

    # Read names CSV dynamically supporting different encodings
    encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252']
    header = []
    rows = []
    
    for encoding in encodings:
        try:
            with open(NAMES_CSV_PATH, mode='r', encoding=encoding) as f:
                reader = csv.reader(f)
                header = next(reader)
                rows = list(reader)
            print(f"[CSV] Loaded CSV successfully using '{encoding}' encoding.")
            break
        except Exception:
            continue

    if not header:
        print("[Error] CSV could not be read or is empty.")
        sys.exit(1)

    # Locate the name column. It should contain "Your Name"
    name_col_idx = -1
    for idx, col in enumerate(header):
        if "Your Name" in col:
            name_col_idx = idx
            break

    if name_col_idx == -1:
        print("[Error] Could not find any column in CSV matching 'Your Name'.")
        print(f"[CSV] Headers found: {header}")
        sys.exit(1)

    print(f"[CSV] Mapping names from column index {name_col_idx}: '{header[name_col_idx]}'")

    # Set up Certificate log column
    if "Certificate" not in header:
        header.append("Certificate")
        cert_col_idx = len(header) - 1
    else:
        cert_col_idx = header.index("Certificate")

    log_rows = []
    success_count = 0
    failed_count = 0

    print(f"\n[Processing] Starting certificate generation for {len(rows)} rows...")

    for idx, row in enumerate(rows):
        # Align row length with header length (excluding certificate if not present in row)
        while len(row) < len(header) - 1:
            row.append("")
        
        name = row[name_col_idx].strip()
        
        # Skip empty name rows
        if not name:
            print(f"  Row {idx + 2}: Skipped (empty name field).")
            if len(row) <= cert_col_idx:
                row.append("Skipped: Empty name")
            else:
                row[cert_col_idx] = "Skipped: Empty name"
            log_rows.append(row)
            continue

        try:
            sanitized_name = sanitize_filename(name)
            base_filename = f"FOSSUOK-DOCKER-PROGRAM-{sanitized_name}"
            output_filename = f"{base_filename}.pdf"

            # Check for duplicate names and append numerical index to avoid overwriting
            counter = 1
            while os.path.exists(os.path.join(OUT_DIR, output_filename)):
                output_filename = f"{base_filename}_{counter}.pdf"
                counter += 1

            # Read template
            template_reader = PdfReader(TEMPLATE_PATH)
            template_page = template_reader.pages[0]
            
            # Fetch width & height in points
            width = float(template_page.mediabox.width)
            height = float(template_page.mediabox.height)

            # Generate overlay
            overlay_packet = create_text_overlay(name, width, height, registered_font)
            overlay_reader = PdfReader(overlay_packet)
            overlay_page = overlay_reader.pages[0]

            # Merge overlay page onto template page
            template_page.merge_page(overlay_page)

            # Write output
            writer = PdfWriter()
            writer.add_page(template_page)
            
            output_filepath = os.path.join(OUT_DIR, output_filename)
            with open(output_filepath, "wb") as out_file:
                writer.write(out_file)

            print(f"  Row {idx + 2}: Generated -> '{output_filename}'")
            
            if len(row) <= cert_col_idx:
                row.append(output_filename)
            else:
                row[cert_col_idx] = output_filename
            success_count += 1

        except Exception as e:
            print(f"  Row {idx + 2} [ERROR]: Failed to generate for '{name}': {e}")
            error_msg = f"Failed: {str(e)}"
            if len(row) <= cert_col_idx:
                row.append(error_msg)
            else:
                row[cert_col_idx] = error_msg
            failed_count += 1

        log_rows.append(row)

    # Write log CSV file in out/ folder
    try:
        with open(LOG_CSV_PATH, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(log_rows)
        print(f"\n[Logging] Certificate log report written to: {LOG_CSV_PATH}")
    except Exception as e:
        print(f"[Logging] ERROR: Could not save log CSV: {e}")

    # Summary report
    print("\n" + "=" * 40)
    print("           GENERATION SUMMARY")
    print("=" * 40)
    print(f"  Total records:         {len(rows)}")
    print(f"  Successfully created:  {success_count}")
    print(f"  Failed records:        {failed_count}")
    print("=" * 40)


if __name__ == "__main__":
    process_certificates()
