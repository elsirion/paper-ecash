#!/usr/bin/env python3
import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path
import shutil
import tempfile

def generate_qr_code(note, output_file, error_correction='M', icon_file=None, icon_size_percent=20):
    """Generate a transparent QR code from an ecash note.

    Args:
        note: The ecash note string to encode
        output_file: Path to save the QR code image
        error_correction: Error correction level (L, M, Q, H). H is recommended when using icons.
        icon_file: Optional path to icon image to overlay in the center of the QR code
        icon_size_percent: Icon size as percentage of QR code width (default: 20)
    """
    try:
        # Generate QR code with qrencode at high resolution
        # -s 20 creates 20 pixels per module for high-quality output
        qr_process = subprocess.Popen(
            ['qrencode', '-l', error_correction, '-s', '20', '-o', '-', note],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if icon_file:
            # If icon is specified, we need to create a temporary QR code first
            temp_qr = output_file + '.temp.png'

            magick_process = subprocess.Popen(
                ['magick', '-', '-transparent', 'white', temp_qr],
                stdin=qr_process.stdout,
                stderr=subprocess.PIPE
            )

            qr_process.stdout.close()
            _, magick_err = magick_process.communicate()

            if magick_process.returncode != 0:
                print(f"Error generating QR code: {magick_err.decode()}")
                return False

            # Calculate proper icon size based on actual pixel dimensions
            # Get QR code dimensions
            qr_info = subprocess.run(
                ['identify', '-format', '%w', temp_qr],
                capture_output=True,
                text=True
            )
            if qr_info.returncode != 0:
                print(f"Error getting QR code dimensions: {qr_info.stderr}")
                return False

            qr_width = int(qr_info.stdout.strip())
            # Calculate icon size based on percentage of QR code width
            icon_size = int(qr_width * (icon_size_percent / 100.0))

            # Overlay the icon in the center with calculated size
            # Using Lanczos filter for best quality when resizing
            overlay_result = subprocess.run(
                [
                    'magick', temp_qr,
                    '(', icon_file,
                    '-filter', 'Lanczos',
                    '-resize', f'{icon_size}x{icon_size}',
                    ')',
                    '-gravity', 'center',
                    '-composite',
                    output_file
                ],
                capture_output=True,
                text=True
            )

            # Clean up temp file
            if os.path.exists(temp_qr):
                os.remove(temp_qr)

            if overlay_result.returncode != 0:
                print(f"Error overlaying icon: {overlay_result.stderr}")
                return False
        else:
            # No icon, just create transparent QR code
            magick_process = subprocess.Popen(
                ['magick', '-', '-transparent', 'white', output_file],
                stdin=qr_process.stdout,
                stderr=subprocess.PIPE
            )

            qr_process.stdout.close()
            _, magick_err = magick_process.communicate()

            if magick_process.returncode != 0:
                print(f"Error generating QR code: {magick_err.decode()}")
                return False

        return True
    except Exception as e:
        print(f"Error generating QR code for note: {e}")
        return False

def generate_latex(qr_files, front_image, back_image, output_tex, qr_x_offset=0, qr_y_offset=0, qr_size=7):
    """Generate LaTeX file with QR codes overlaid on front images.

    Args:
        qr_files: List of QR code image file paths
        front_image: Path to front image
        back_image: Path to back image
        output_tex: Output LaTeX file path
        qr_x_offset: QR code X offset in cm (distance from left edge)
        qr_y_offset: QR code Y offset in cm (distance from bottom edge)
        qr_size: QR code size in cm
    """

    # LaTeX template based on main.tex
    latex_template = r"""\documentclass[a4paper]{article}
\usepackage[margin=0cm, paperwidth=21cm, paperheight=29.7cm]{geometry}
\usepackage{graphicx}
\usepackage{tikz}
\usepackage{calc}
% ===== CONFIGURATION VARIABLES =====
% Image dimensions
\newlength{\imgwidth}
\newlength{\imgheight}
\setlength{\imgwidth}{14cm}
\setlength{\imgheight}{7cm}
% QR code positioning (relative to bottom-left of front image)
\newlength{\qrxoffset}
\newlength{\qryoffset}
\setlength{\qrxoffset}{""" + f"{qr_x_offset}cm" + r"""}  % Distance from left edge
\setlength{\qryoffset}{""" + f"{qr_y_offset}cm" + r"""}  % Distance from bottom edge
% QR code size
\newlength{\qrsize}
\setlength{\qrsize}{""" + f"{qr_size}cm" + r"""}
% Spacing between images
\newlength{\vspacing}
\setlength{\vspacing}{0cm}  % Vertical spacing between images
% Page margins
\newlength{\pagemargin}
\setlength{\pagemargin}{0cm}
% ===================================
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
% Command to create one image with QR overlay
% Usage: \overlayimage{front_image.png}{qr_code.png}
\newcommand{\overlayimage}[2]{%
	\begin{tikzpicture}
		% Base image
		\node[anchor=south west, inner sep=0pt] (base) at (0,0) {%
			\includegraphics[width=\imgwidth, height=\imgheight]{#1}%
		};
		% QR code overlay
		\node[anchor=south west, inner sep=0pt] at (\qrxoffset, \qryoffset) {%
			\includegraphics[width=\qrsize, height=\qrsize]{#2}%
		};
		% Cutting lines
		\draw[thin, dashed, lightgray] (0,0) -- (\imgwidth,0); % Bottom cutting line
		\draw[thin, dashed, lightgray] (0,\imgheight) -- (\imgwidth,\imgheight); % Top cutting line
		\draw[thin, dashed, lightgray] (\imgwidth,0) -- (\imgwidth,\imgheight); % Right cutting line
	\end{tikzpicture}%
}
% Command to create back image (no QR overlay)
% Usage: \backimage{back_image.png}
\newcommand{\backimage}[1]{%
	\begin{tikzpicture}
		% Back image
		\node[anchor=south west, inner sep=0pt] (base) at (0,0) {%
			\includegraphics[width=\imgwidth, height=\imgheight]{#1}%
		};
	\end{tikzpicture}%
}
\begin{document}
"""
    
    # Generate pages with 4 notes per page
    notes_per_page = 4
    num_pages = (len(qr_files) + notes_per_page - 1) // notes_per_page
    
    content = latex_template
    
    for page_idx in range(num_pages):
        # Front page
        content += "\t% ===== PAGE {} (FRONT) =====\n".format(page_idx * 2 + 1)
        content += "\t\\begin{tikzpicture}[remember picture, overlay]\n"
        
        start_idx = page_idx * notes_per_page
        end_idx = min(start_idx + notes_per_page, len(qr_files))
        
        for i, note_idx in enumerate(range(start_idx, end_idx)):
            if i == 0:
                content += "\t\t% First image (top)\n"
                content += "\t\t\\node[anchor=north west, inner sep=0pt] at ([xshift=\\pagemargin, yshift=-\\pagemargin]current page.north west) {%\n"
            else:
                content += f"\t\t% Image {i+1}\n"
                content += f"\t\t\\node[anchor=north west, inner sep=0pt] at ([xshift=\\pagemargin, yshift=-\\pagemargin-{i}\\imgheight-{i}\\vspacing]current page.north west) {{%\n"
            
            content += f"\t\t\t\\overlayimage{{{front_image}}}{{{qr_files[note_idx]}}}%\n"
            content += "\t\t};\n"
        
        content += "\t\\end{tikzpicture}\n\n"
        content += "\t\\newpage\n\n"
        
        # Back page
        content += "\t% ===== PAGE {} (BACK) =====\n".format(page_idx * 2 + 2)
        content += "\t% For duplex printing, backs are RIGHT-ALIGNED to align when flipped\n"
        content += "\t\\begin{tikzpicture}[remember picture, overlay]\n"
        
        for i in range(end_idx - start_idx):
            if i == 0:
                content += "\t\t% First back (top) - aligns with first front\n"
                content += "\t\t\\node[anchor=north east, inner sep=0pt] at ([xshift=-\\pagemargin, yshift=-\\pagemargin]current page.north east) {%\n"
            else:
                content += f"\t\t% Back {i+1}\n"
                content += f"\t\t\\node[anchor=north east, inner sep=0pt] at ([xshift=-\\pagemargin, yshift=-\\pagemargin-{i}\\imgheight-{i}\\vspacing]current page.north east) {{%\n"
            
            content += f"\t\t\t\\backimage{{{back_image}}}%\n"
            content += "\t\t};\n"
        
        content += "\t\\end{tikzpicture}\n\n"
        
        if page_idx < num_pages - 1:
            content += "\t\\newpage\n\n"
    
    content += "\\end{document}\n"
    
    with open(output_tex, 'w') as f:
        f.write(content)

def compile_latex(tex_file, output_dir):
    """Compile LaTeX file to PDF."""
    try:
        # Run pdflatex twice to ensure proper rendering
        for _ in range(2):
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', output_dir, tex_file],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"LaTeX compilation error: {result.stderr}")
                return False
        return True
    except Exception as e:
        print(f"Error compiling LaTeX: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate PDF with ecash QR codes from CSV file')
    parser.add_argument('csv_file', help='CSV file containing ecash notes (one per line)')
    parser.add_argument('--front-image', default='front.png', help='Base image for front side (default: front.png)')
    parser.add_argument('--back-image', default='back.png', help='Back image (default: back.png)')
    parser.add_argument('--output', default='ecash_notes.pdf', help='Output PDF file (default: ecash_notes.pdf)')
    parser.add_argument('--qr-dir', default='qr_codes', help='Directory for QR code images (default: qr_codes)')
    parser.add_argument('--qr-icon', help='Optional icon image to overlay in center of QR code')
    parser.add_argument('--qr-icon-size', type=float, default=20,
                        help='Icon size as percentage of QR code width (default: 20, max ~30 with H error correction)')
    parser.add_argument('--qr-error-correction', default='M', choices=['L', 'M', 'Q', 'H'],
                        help='QR code error correction level: L(7%%), M(15%%), Q(25%%), H(30%%). Use H when overlaying icons. (default: M, or H if --qr-icon is used)')
    parser.add_argument('--qr-x-offset', type=float, default=0,
                        help='QR code X position offset in cm from left edge (default: 0)')
    parser.add_argument('--qr-y-offset', type=float, default=0,
                        help='QR code Y position offset in cm from bottom edge (default: 0)')
    parser.add_argument('--qr-size', type=float, default=7,
                        help='QR code size in cm (default: 7)')

    args = parser.parse_args()

    # Auto-set error correction to H if icon is provided and user didn't specify
    if args.qr_icon and args.qr_error_correction == 'M':
        args.qr_error_correction = 'H'
        print(f"Note: Using error correction level H (30%%) for QR codes with icon overlay")

    # Verify required files exist
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file '{args.csv_file}' not found")
        sys.exit(1)

    if args.qr_icon and not os.path.exists(args.qr_icon):
        print(f"Error: Icon file '{args.qr_icon}' not found")
        sys.exit(1)

    if not os.path.exists(args.front_image):
        print(f"Warning: Base image '{args.front_image}' not found. Make sure it exists before running LaTeX.")

    if not os.path.exists(args.back_image):
        print(f"Warning: Back image '{args.back_image}' not found. Make sure it exists before running LaTeX.")
    
    # Create QR codes directory
    qr_dir = Path(args.qr_dir)
    qr_dir.mkdir(exist_ok=True)
    
    # Read CSV and generate QR codes
    qr_files = []
    print(f"Reading notes from {args.csv_file}...")
    
    with open(args.csv_file, 'r') as csvfile:
        # Simple line-by-line reading (no CSV parsing needed for single column)
        notes = [line.strip() for line in csvfile if line.strip()]
    
    print(f"Found {len(notes)} notes. Generating QR codes...")
    
    for i, note in enumerate(notes, 1):
        qr_filename = f"ecash_{i:04d}.png"
        qr_path = qr_dir / qr_filename

        print(f"Generating QR code {i}/{len(notes)}: {qr_filename}")
        if generate_qr_code(note, str(qr_path), error_correction=args.qr_error_correction,
                           icon_file=args.qr_icon, icon_size_percent=args.qr_icon_size):
            qr_files.append(str(qr_path))
        else:
            print(f"Failed to generate QR code for note {i}")
    
    if not qr_files:
        print("Error: No QR codes were generated successfully")
        sys.exit(1)
    
    print(f"\nGenerated {len(qr_files)} QR codes successfully")
    
    # Generate LaTeX file
    tex_file = 'ecash_notes.tex'
    print(f"\nGenerating LaTeX file: {tex_file}")
    generate_latex(qr_files, args.front_image, args.back_image, tex_file,
                   qr_x_offset=args.qr_x_offset, qr_y_offset=args.qr_y_offset, qr_size=args.qr_size)
    
    # Compile to PDF
    print(f"\nCompiling LaTeX to PDF: {args.output}")
    if compile_latex(tex_file, '.'):
        pdf_path = tex_file.replace('.tex', '.pdf')
        if pdf_path != args.output:
            shutil.move(pdf_path, args.output)
        print(f"\nSuccess! PDF generated: {args.output}")
        
        # Clean up auxiliary LaTeX files
        for ext in ['.aux', '.log']:
            aux_file = tex_file.replace('.tex', ext)
            if os.path.exists(aux_file):
                os.remove(aux_file)
    else:
        print("\nError: Failed to compile LaTeX to PDF")
        sys.exit(1)

if __name__ == '__main__':
    main()
