#!/usr/bin/env python3
"""
PDF Image Compression Utility
----------------------------
This script compresses PDF files by extracting internal images, compressing them
using Pillow (JPEG quality 75-80, optimized encoding), and replacing them back
in the PDF structure. This achieves significant file size reduction without any
noticeable loss of visual quality.

Usage:
  1. Compress a single template file:
     python app/compress_pdf.py --input src/docker-certificate.pdf --output src/docker-certificate-compressed.pdf

  2. Compress an entire folder of certificates:
     python app/compress_pdf.py --dir out --out-dir out_compressed
"""

import os
import sys
import io
import argparse
from pypdf import PdfReader, PdfWriter
from PIL import Image


def compress_pdf(input_path, output_path, quality=80):
    """
    Compress a single PDF by opening it, resizing/compressing all JPEG/PNG images,
    and writing it back out.
    """
    if not os.path.exists(input_path):
        print(f"[Error] Input PDF file does not exist: {input_path}")
        return False

    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        # Copy pages to writer
        writer.append(reader)
        
        # Optimize images on all pages of the writer
        for page_idx, page in enumerate(writer.pages):
            images = page.images
            if not images:
                continue
            
            for img_name, img_file in images.items():
                try:
                    # Open original image bytes using PIL
                    img = Image.open(io.BytesIO(img_file.data))
                    
                    # Check image color mode. Convert RGBA to RGB for JPEG compression
                    # if transparency is not needed.
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        # Save transparent PNG with optimization
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='PNG', optimize=True)
                        compressed_data = img_byte_arr.getvalue()
                        # Only replace if the optimized data is actually smaller
                        if len(compressed_data) < len(img_file.data):
                            img_file.replace(img, quality=quality)
                    else:
                        # Save JPEG with specified quality
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
                        compressed_data = img_byte_arr.getvalue()
                        if len(compressed_data) < len(img_file.data):
                            img_file.replace(img, quality=quality)
                except Exception as e:
                    print(f"    [Warning] Could not optimize image {img_name} on page {page_idx+1}: {e}")

        # Ensure output directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        with open(output_path, "wb") as f:
            writer.write(f)

        orig_size = os.path.getsize(input_path)
        new_size = os.path.getsize(output_path)
        reduction = (orig_size - new_size) / orig_size * 100
        print(f"  Compressed: {os.path.basename(input_path)}")
        print(f"  Size: {orig_size/1024/1024:.2f} MB -> {new_size/1024/1024:.2f} MB (-{reduction:.1f}%)")
        return True
    except Exception as e:
        print(f"[Error] Failed to compress {input_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Compress PDF files by optimizing internal images.")
    parser.add_argument("--input", "-i", help="Path to single input PDF file")
    parser.add_argument("--output", "-o", help="Path to output compressed PDF file (used with --input)")
    parser.add_argument("--dir", "-d", help="Directory containing PDF files to compress")
    parser.add_argument("--out-dir", "-out", help="Directory where compressed PDFs will be saved (used with --dir)")
    parser.add_argument("--quality", "-q", type=int, default=80, help="JPEG compression quality (1-100, default: 80)")

    args = parser.parse_args()

    # Mode 1: Single file compression
    if args.input:
        if not args.output:
            print("[Error] Please specify the output path using --output or -o")
            sys.exit(1)
        success = compress_pdf(args.input, args.output, args.quality)
        sys.exit(0 if success else 1)

    # Mode 2: Folder compression
    elif args.dir:
        if not args.out_dir:
            print("[Error] Please specify the output directory using --out-dir or -out")
            sys.exit(1)
        
        if not os.path.exists(args.dir):
            print(f"[Error] Input directory does not exist: {args.dir}")
            sys.exit(1)

        os.makedirs(args.out_dir, exist_ok=True)
        pdf_files = [f for f in os.listdir(args.dir) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"No PDF files found in directory: {args.dir}")
            sys.exit(0)

        print(f"Found {len(pdf_files)} PDF files in '{args.dir}'. Starting compression (Quality={args.quality})...")
        success_count = 0
        
        for f in pdf_files:
            in_path = os.path.join(args.dir, f)
            out_path = os.path.join(args.out_dir, f)
            if compress_pdf(in_path, out_path, args.quality):
                success_count += 1
                
        print(f"\nCompression complete! Successfully compressed {success_count}/{len(pdf_files)} files.")
        print(f"Compressed certificates folder: {args.out_dir}")
        sys.exit(0)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
