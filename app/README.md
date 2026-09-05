# FOSS Certificate Automation Script

This Python utility automates the generation of customized certificates by reading recipient names from a CSV file and overlaying them onto a PDF template using the **Montserrat Medium** font.

---

## Features

1. **Crisp Vector Overlay:** Draws text directly onto the PDF using `reportlab` and `pypdf`, preserving the template's high-quality vectors without rasterization or pixelation.
2. **Montserrat Medium Font:** Automatically downloads the official `Montserrat-Medium.ttf` font from Google Fonts at runtime if not already present in the folder.
3. **Dynamic Font Scaling:** Intelligently scales down the font size for very long names (e.g. triple or quadruple names) so they never clip or wrap off the page margins.
4. **Horizontal & Vertical Alignment:** Positions names centered horizontally and exactly **0.38 of the height from the top** of the certificate.
5. **Robust CSV Processing:** Dynamically matches columns containing `"Your Name"`, ignoring differences in whitespace, index numbers, or formatting prefix.
6. **Detailed Log Copy:** Generates a copy of the CSV with an added `Certificate` column mapping names to their respective output PDF filenames, making it trivial to automate email distribution later.

---

## Directory Structure

```text
foss-certificate-automation/
├── app/
│   ├── generate_certificates.py   # Main Python automation script
│   ├── requirements.txt           # Python package dependencies
│   └── README.md                  # This documentation file
├── src/
│   ├── docker-certificate.pdf    # PDF template (11.693" x 8.267" A4)
│   └── names.csv                  # Recipient CSV list
└── out/                           # Output directory (Created automatically)
    ├── FOSSUOK-DOCKER-PROGRAM-<Name>.pdf
    └── names_applied_log.csv      # Log mapping names to filenames
```

---

## Installation & Setup

1. **Ensure Python is Installed:**
   The script requires Python 3.6 or higher. Check your version with:
   ```bash
   python --version
   ```

2. **Navigate to the Project Directory:**
   ```bash
   cd foss-certificate-automation
   ```

3. **Install Dependencies:**
   Install required Python packages using `pip`:
   ```bash
   pip install -r app/requirements.txt
   ```

---

## How to Run

Execute the script from the project root directory:

```bash
python app/generate_certificates.py
```

### What happens behind the scenes:
- The script checks if `Montserrat-Medium.ttf` is present in the `app/` or `src/` folders. If not, it automatically downloads it.
- It parses `src/names.csv` and finds the name column containing `Your Name`.
- It processes each name, calculates the coordinates, merges the text vector overlay onto `src/docker-certificate.pdf`, and saves it to `out/FOSSUOK-DOCKER-PROGRAM-<Name>.pdf`.
- It creates a duplicate CSV log file in `out/names_applied_log.csv` indicating success/failure and the exact generated filename.

---

## Customization

Instead of modifying the script code, you can open and edit the **[`app/config.json`](file:///d:/dev/repo/gh-pm-com/foss-certificate-automation/app/config.json)** file:

* **`font_size`**: Change the text size (currently set to `16.50` pt).
* **`top_offset_ratio`**: Adjust the position height from the top of the certificate (currently `0.40`, meaning 40% from the top).
* **`text_color_rgb`**: Modify the RGB values (between `0.0` and `1.0`) to change the font color.
* **`font_url` / `font_name` / `font_filename`**: Modify these to load a different custom font if needed.

