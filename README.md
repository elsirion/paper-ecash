# How to make ecash notes from these designs:

From within your working dir, run:

```bash
../../generate_ecash_pdf.py  --front-image ../../contrib/historic/front.png --back-image ../../contrib/historic/back.png --qr-icon ../../contrib/historic/qr_overlay.png --qr-size 4.8 --qr-x-offset 1.65 --qr-y-offset 1.13 --qr-error-correction Q notes.csv
```
