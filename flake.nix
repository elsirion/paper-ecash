{
  description = "Paper eCash PDF generator with QR codes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    fedimint.url = "github:elsirion/fedimint?ref=2025-08-exact-spends";
  };

  outputs = { self, nixpkgs, flake-utils, fedimint }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python environment with required packages
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          # Add any additional Python packages if needed
        ]);
        
        # TeXLive with required packages
        texliveEnv = pkgs.texliveFull;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Python
            pythonEnv
            
            # LaTeX
            texliveEnv
            
            # Image processing
            imagemagick
            qrencode
            
            # Utilities
            coreutils
            gnused
            gnugrep
            
            # Development tools (optional but useful)
            direnv
            nix-direnv
            fedimint.packages.${system}.fedimint-cli
          ];
          
          shellHook = ''
            echo "Paper eCash PDF Generator Environment"
            echo "--------------------------------------"
            echo "Available commands:"
            echo "  python generate_ecash_pdf.py <csv_file> - Generate PDF from CSV"
            echo "  qrencode - Generate QR codes"
            echo "  magick - ImageMagick for image processing"
            echo "  pdflatex - LaTeX compiler"
            echo ""
            echo "Example usage:"
            echo "  python generate_ecash_pdf.py notes.csv --output ecash.pdf"
            echo ""
            
            # Make the Python script executable
            if [ -f "generate_ecash_pdf.py" ]; then
              chmod +x generate_ecash_pdf.py
            fi
          '';
        };
        
        # Optional: Create an app that can be run with `nix run`
        apps.default = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "generate-ecash" ''
            #!${pkgs.bash}/bin/bash
            export PATH="${pythonEnv}/bin:${texliveEnv}/bin:${pkgs.imagemagick}/bin:${pkgs.qrencode}/bin:$PATH"
            exec ${pythonEnv}/bin/python ${./generate_ecash_pdf.py} "$@"
          ''}/bin/generate-ecash";
        };
      });
}
