# Paper Ecash Generator
For the commands below to work you should enter the nix develop shell shipped with the project. If you have [already installed Nix](https://github.com/DeterminateSystems/nix-installer) or are running NixOS simply run `nix develop` in a shell inside the project directory. The dev shell gives you a modified `fedimint-cli` command that is able to efficiently issue exact denomination ecash.

## Generating raw ecash
To generate ecash notes you first have to decide on an amount for each physical ecash note. You can use [notes.sirion.io](https://notes.sirion.io/) to explore possible denomination combinations. It's recommended to stay below 4 denominations to keep the QR code scannable. Once you have decided on the amount, run the following command after joining and funding the wallet you are using (replace `/path/to/wallet` accordingly). You can replace `1048576` with the comma separated list outputted by the denomination selector.

```
for NUM in {0..99}; do fedimint-cli --data-dir /path/to/wallet module mint spend-exact --include-invite 1048576 | jq -r .notes >> notes.csv; echo "done $NUM"; done
```

This will produce a `notes.csv` file with ecash notes without expiry. If you lose the file the money is gone. It's advisable to keep it around to eventually reclaim unused notes or to check the claim rate.

## Generating paper notes
`notes.csv` can then be fed into `generate_ecash_pdf.py`:

```
usage: generate_ecash_pdf.py [-h] [--front-image FRONT_IMAGE] [--back-image BACK_IMAGE] [--output OUTPUT] [--qr-dir QR_DIR] [--qr-icon QR_ICON] [--qr-icon-size QR_ICON_SIZE] [--qr-error-correction {L,M,Q,H}]
                             [--qr-x-offset QR_X_OFFSET] [--qr-y-offset QR_Y_OFFSET] [--qr-size QR_SIZE]
                             csv_file

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
  --qr-icon QR_ICON     Optional icon image to overlay in center of QR code
  --qr-icon-size QR_ICON_SIZE
                        Icon size as percentage of QR code width (default: 20, max ~30 with H error correction)
  --qr-error-correction {L,M,Q,H}
                        QR code error correction level: L(7%), M(15%), Q(25%), H(30%). Use H when overlaying icons. (default: M, or H if --qr-icon is used)
  --qr-x-offset QR_X_OFFSET
                        QR code X position offset in cm from left edge (default: 0)
  --qr-y-offset QR_Y_OFFSET
                        QR code Y position offset in cm from bottom edge (default: 0)
  --qr-size QR_SIZE     QR code size in cm (default: 7)
```

This will generate a folder with the QR codes, a tex file and a bunch of LaTeX helper files. It's advisable to run the command in a new directory inside the notes folder (which is in `.gitignore`).

## Front and back images
You can find some examples of front and back images in `/contrib`. Please remix them and add yours!

