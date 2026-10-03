Drop PDFs of your papers here (any file name). They are NOT published on the website
(folders starting with "_" are skipped by GitHub Pages). They are only used to make a
picture of the first page for each publication page.

Then run:  python3 publications/_src/build.py

The build matches each PDF to a publication by its DOI or title. A PDF named
<page-name>.pdf (e.g. 2019-voter-equalization-turnout-bias-after-electoral-reform.pdf)
always matches. To also offer a public download, put the PDF in publications/pdf/ instead.
