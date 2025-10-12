# Paper ecash generation
## Generating raw ecash
To generate ecash notes run the following command after joining and funding the wallet you are using (replace `/path/to/wallet` accordingly):

```
for NUM in {0..99}; do nix run github:elsirion/fedimint?ref=2025-08-exact-spends#fedimint-cli -- --data-dir /path/to/wallet module mint spend-exact --include-invite 1048576 | jq -r .notes >> notes.csv; echo "done $NUM"; done
```

This will produce a `notes.csv` filei with ecash notes without expiry. If you lose the file the money is gone. It's advisable to keep it around to eventually reclaim unused notes or to check the claim rate.

## Generating paper notes
`notes.csv` can then be fed into `generate_ecash_pdf.py`:

```
usage: generate_ecash_pdf.py [-h] [--front-image FRONT_IMAGE] [--back-image BACK_IMAGE] [--output OUTPUT] [--qr-dir QR_DIR] csv_file

Generate PDF with ecash QR codes from CSV file

positional arguments:
  csv_file              CSV file containing ecash notes (one per line)

options:
  -h, --help            show this help message and exit
  --front-image FRONT_IMAGE
                        Base image for front side (default: front.png)
  --back-image BACK_IMAGE
                        Back image (default: back.png)
  --output OUTPUT       Output PDF file (default: ecash_notes.pdf)
  --qr-dir QR_DIR       Directory for QR code images (default: qr_codes)
```

This will generate a folder with the QR codes, a tex file and a bunch of LaTeX helper files. It's advisable to run the command in a new directory inside the notes folder (which is in `.gitignore`).

## Front and back images
You can find some examples of front and back images in `/contrib`. Please remix them and add yours!
