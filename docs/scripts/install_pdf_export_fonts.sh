#!/bin/sh
# Install the fonts needed to export the mid-defense deck to PDF on Linux.
#
# The deck specifies Times New Roman throughout (matching the university
# template) and Consolas for code blocks. Neither ships with Linux, so
# LibreOffice silently substitutes them and the exported PDF embeds the
# substitute instead. Layout is unaffected -- Liberation Serif is
# metric-compatible with Times New Roman -- but the PDF is then not the
# typeface the department's template calls for.
#
# Times New Roman comes from Microsoft's Core Fonts for the Web, whose EULA
# permits redistribution only in the original installer form. The font files
# are therefore downloaded here rather than committed to the repository, and
# each download is checked against the SHA-256 recorded by Debian's
# ttf-mscorefonts-installer package.
#
# Usage:  sudo sh docs/scripts/install_pdf_export_fonts.sh
#
# Not needed on Windows, where PowerPoint has both fonts already.

set -e

FONTDIR=/usr/share/fonts/truetype/msttcorefonts
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

# times32.exe carries Times New Roman regular, bold, italic and bold-italic.
URL="https://downloads.sourceforge.net/project/corefonts/the%20fonts/final/times32.exe"
SHA256="db56595ec6ef5d3de5c24994f001f03b2a13e37cee27bc25c58f6f43e8f807ab"

if ! command -v cabextract >/dev/null 2>&1; then
    echo "cabextract is required: apt-get install -y cabextract" >&2
    exit 1
fi

echo "Downloading Times New Roman (Microsoft Core Fonts for the Web)..."
curl -sS -L --max-time 120 -o "$WORKDIR/times32.exe" "$URL"

echo "$SHA256  $WORKDIR/times32.exe" | sha256sum -c - >/dev/null || {
    echo "Checksum mismatch -- refusing to install the downloaded file." >&2
    exit 1
}

cabextract -L -q -d "$WORKDIR" "$WORKDIR/times32.exe"
mkdir -p "$FONTDIR"
cp "$WORKDIR"/times*.ttf "$FONTDIR"/

# Consolas is not part of the core fonts package and is not redistributable,
# so the code blocks on the worked-example slide are substituted on Linux
# either way. Liberation Mono is chosen over the default DejaVu Sans Mono
# fallback purely for letterform preference, not for metrics: both advance
# 0.60 em against Consolas's 0.55, i.e. they are within 0.3% of each other.
#
# Layout is unaffected by any of the three. The longest code line is 71
# characters at 11pt, which occupies 5.96" in Consolas and 6.53" in the
# widest substitute, against 10.6" of available width -- so nothing wraps
# differently. If an exact-looking match matters, Cascadia Mono (MIT, and
# Consolas's modern successor) can be vendored and named in the deck
# instead; that is a deliberate design change, not a packaging fix.
cat > /etc/fonts/conf.d/70-consolas-substitute.conf <<'CONF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <alias binding="strong">
    <family>Consolas</family>
    <prefer><family>Liberation Mono</family></prefer>
  </alias>
</fontconfig>
CONF

fc-cache -f >/dev/null 2>&1

echo
echo "Installed:"
fc-match "Times New Roman"
fc-match "Times New Roman:bold"
fc-match "Times New Roman:italic"
fc-match "Consolas"
echo
echo "Now re-export the PDF:"
echo "  soffice --headless --convert-to pdf --outdir docs/scripts \\"
echo "    docs/scripts/Md_Riaz_Mid_Defense_Final_0322310105101024.pptx"
