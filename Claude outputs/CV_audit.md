# CV and website consistency audit (3 Oct 2026)

Status. All 30 points of the earlier audit are applied to `cv.pdf` (source in `Claude outputs/cv.tex`, build with pdflatex).

## Checked
- Every DOI on the CV appears in `publications/_src/publications.json` and every DOI in the JSON appears on the CV (53 DOIs).
- Same 72 publications in both (1 book, 18 articles, 10 chapters, 5 reviews, 2 datasets, 26 Ideas, 2 reports, 8 working papers).
- Years, volumes, issues, pages and Ideas numbers match between the CV and the JSON.

## Changed on the website
- `cv.pdf` replaced with the updated CV.
- All 13 pages that linked the old Dropbox CV (`CV_Kenneth_Bunker.pdf`) now link to `https://kennethbunker.github.io/cv.pdf`.
- Home page "Selected publications" updated. LGS now 2026 online first, SSCR 44(4) 595-616, JPI 31(3) 905-922, HSSC 12 1911, Party Politics 2024, REP issue 186 only, RChD Spanish title, Cambridge book title and pages, review entries with DOIs, LAPS author order, chronological order.
- Ideas #9 and #10 swapped in `publications.json` to match the PDFs (#9 velocidad, Olavarría; #10 hora y precisión, Jofré). Page URLs (slugs) kept unchanged so existing links and Google Scholar records still work.

## Changed on the CV to match the publishers
- REDCP 2010 title "Explicando la desproporcionalidad en América Latina. Magnitud de distrito, malapportionment y fragmentación partidaria".
- LGS title uses "Vote–Seat".
- Política 2016 journal name "Política. Revista de Ciencia Política".

## Still open
- UCEN notes keep their 2018 titles (the PDFs cover 1990-2018). ResearchGate lists them as "... 1990-2022".
- labdemgob.github.io (separate repo) still lists Ideas #9 and #10 the other way round.
