# FOSS Certificate Automation

A small Python utility for generating personalized PDF certificates from a CSV file and a PDF template. Recipient names are drawn onto the template using ReportLab and merged with `pypdf`.

## Requirements

- Python 3.6 or newer
- A certificate PDF template at `src/docker-certificate.pdf`
- A recipient CSV at `src/names.csv`

Install the Python dependencies from the repository root:

```bash
python -m pip install -r app/requirements.txt
```

## CSV Format

The generator needs a header containing the text `Your Name` (case-sensitive). The header may include a form index or extra whitespace, for example:

```csv
3. Your Name
Example Recipient
Another Recipient
```

Only the first matching `Your Name` column is used. Additional columns are allowed and are copied to the output log. A common form-export format is also supported:

```csv
Timestamp,Email address,1. Index Number,2. Mobile Number,3. Your Name,4. Email Address,5. Certificate Preference
2026-09-05 09:00:00,example@example.com,I-001,0712345678,Example Recipient,example@example.com,E-Certificate
```

The repository includes two safe CSV templates:

- `src/names.example.csv` contains an example recipient name.
- `src/names.csv` is the working input and contains `CHANGE OR REPLACE BY USER`.

Replace the row in `src/names.csv` with real recipients before generating certificates. Other recipient CSV files are ignored by Git. Do not commit personal information such as names, email addresses, or phone numbers.

The repository also includes `src/docker-certificate.example.pdf`, a dummy PDF for the expected template location. Copy your real certificate template to `src/docker-certificate.pdf` before running the generator. The real template is ignored by Git because it may contain private or event-specific artwork.

## Generate Certificates

Run this command from the repository root:

```bash
python app/generate_certificates.py
```

The generator:

1. Reads names from `src/names.csv`.
2. Uses `src/docker-certificate.pdf` as the template.
3. Downloads the configured font into `app/` if it is not already available.
4. Writes one PDF per recipient to `out/`.
5. Writes `out/names_applied_log.csv`, which includes the generated certificate filename.

Generated files are ignored by Git.

## Compress Certificates

Compress all generated certificates into `out_compressed/`:

```bash
python app/compress_pdf.py --dir out --out-dir out_compressed
```

Compress one PDF to a chosen destination:

```bash
python app/compress_pdf.py --input src/docker-certificate.pdf --output src/docker-certificate-compressed.pdf
```

Use `--quality` to change JPEG compression quality for embedded images. The default is `80`:

```bash
python app/compress_pdf.py --dir out --out-dir out_compressed --quality 75
```

## Configuration

Edit `app/config.json` to customize certificate rendering:

- `font_size`: Starting font size in points.
- `top_offset_ratio`: Vertical placement measured from the top of the page.
- `font_name`, `font_filename`, `font_url`: Font registration and download settings.
- `text_color_rgb`: Text color as three values between `0.0` and `1.0`.
- `max_text_width_ratio`: Maximum name width as a fraction of the page width.

Long names are automatically scaled down to fit the configured width.

## Project Layout

```text
foss-certificate-automation/
├── app/
│   ├── compress_pdf.py
│   ├── config.json
│   ├── generate_certificates.py
│   └── requirements.txt
├── src/
│   ├── docker-certificate.pdf       # Local template; ignored by Git
│   └── docker-certificate.example.pdf # Safe dummy template
│   ├── names.csv          # Local working input; replace the placeholder row
│   └── names.example.csv  # Safe CSV format example
├── out/                 # Generated certificates and processing log
└── out_compressed/     # Compressed generated certificates
```
