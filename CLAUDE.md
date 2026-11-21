# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O repozitáři

Výukové prezentace předmětu Teoretická informatika (SPŠE Ječná) psané v LaTeXu, třída Beamer. Repozitář neobsahuje aplikační kód — jediným programem je `compile.py`, který obaluje `pdflatex`. Obsah, komentáře v kódu i commit messages jsou česky.

Každá prezentace je adresář `ti-NN-nazev/` s hlavním souborem `main.tex`. Adresáře `ti-99-*` jsou doplňkové či rozpracované materiály; `--all` je zpracuje také.

## Kompilace

Všechny příkazy se spouštějí z kořenového adresáře repozitáře.

Jedna prezentace:

```bash
python compile.py -f ti-04-dijkstra -t ti-04-dijkstra -ar 43 1610
```

Všechny prezentace včetně handoutů, s přesunem PDF do kořene:

```bash
python compile.py --all --handout --move -ar 43 1610
```

Bez `-ar` se použije poměr stran zapsaný v `main.tex` (dnes všude `43`). `--handout` vytvoří handout pro *každý* požadovaný poměr. Výstup se jmenuje `<title>[_<pomer>][_handout].pdf`, u `--all` se `<title>` odvodí z názvu adresáře.

Neexistují testy ani linter. Ověřením změny je úspěšná kompilace a vizuální kontrola PDF ve všech používaných poměrech stran.

## Jak compile.py funguje

Každá varianta se překládá v **dočasné pracovní kopii** mimo repozitář (`create_workspace()`): adresář v systémovém `tmp`, který zrcadlí kořen repozitáře symbolickými odkazy (bez nich, typicky na Windows, kopiemi). Adresář prezentace je v kopii skutečný a pdflatex do něj zapisuje; v repozitáři tak nevznikají žádné pomocné soubory ani `pdfa.xmpi`. Pro každou variantu kromě té úplně základní se do kopie vygeneruje `main_<aspect>[_handout].tex`, v němž se regulárním výrazem přepíšou volby v řádku `\documentclass` (nahradí `aspectratio=`, přidá/odebere `handout`). Varianta se zkompiluje v pořadí `pdflatex`, `biber`, `pdflatex`, `pdflatex`, PDF se přesune do adresáře prezentace pod výsledným jménem a kopie se smaže.

`pdflatex` běží v kořeni pracovní kopie s `-output-directory <adresář prezentace>`, `biber` s pracovním adresářem prezentace. Relativní cesty ve zdrojích (`../assets/...`, `images/...`, `ti-16-kryptografie/images/...`) se proto řeší stejně jako při překladu z kořene repozitáře a do PDF se nedostane absolutní cesta z disku.

Izolace je důvod, proč se smí překládat souběžně i varianty téže prezentace: `pdfx` při každém průchodu zapisuje `pdfa.xmpi` pod pevným jménem a ve sdíleném adresáři by si jej varianty přepisovaly. Počet souběžných překladů určuje `-j` (výchozí je počet jader; s `--verbose` jedna). Hlášení o variantě se vypisuje vcelku až po jejím dokončení.

Nezměněné varianty se nepřekládají. Po úspěšném překladu se do `.compile-cache/<adresář>/<pdf>.json` uloží otisky (SHA-256 obsahu) všech souborů, které pdflatex přečetl (seznam dává `-recorder`, soubor `.fls`), databáze `.bib` z `.bcf`, samotného `compile.py` a výsledného PDF. Varianta se přeskočí, jen když sedí všechny otisky a PDF existuje v adresáři prezentace nebo (s `--move`) v cílovém adresáři. `--force` přeloží vše. Při podezření na zastaralý výstup stačí `.compile-cache/` smazat.

Výstup nástrojů se zachytává; skript tiskne jen řádek na variantu (počet stran, velikost, čas) a po neúspěchu vypíše z `.log` místo chyby s okolními řádky vstupu. Nerozřešené odkazy a citace hlásí jako varování. Neúspěšná varianta překlad dalších nezastaví, skript ale skončí s návratovým kódem `1`. Syrový výstup vrátí `--verbose`.

Důsledky pro editaci zdrojů:

- `\documentclass[...]{beamer}` musí zůstat na **jednom řádku**; jinak jej regulární výraz v `update_documentclass_options()` nerozpozná a varianta se vygeneruje beze změny voleb.
- Volbu `handout` nepiš natvrdo do `main.tex` — skript ji u generovaných variant vždy odstraní a doplní podle `--handout`.
- Dočasný `main_*.tex` vzniká jen v pracovní kopii. Pokud takový soubor v adresáři prezentace je, jde o zbytek po starší verzi skriptu a do commitu nepatří.

## Struktura prezentace

`main.tex` má ustálenou hlavičku; pořadí `\input` je závazné (`theme` používá barvy z `packages`, `macros` staví na obojím):

```latex
\documentclass[11pt,professionalfont,aspectratio=43]{beamer}

\input{../assets/packages.tex}
\input{../assets/theme.tex}
\input{../assets/macros.tex}
\input{../assets/listing.tex}

\def\presentationtitle{Název prezentace}

\begin{document}
    \input{../titlepage.tex}
    ...
\end{document}
```

Sdílené soubory a jejich role:

- `assets/packages.tex` — balíčky. `pdfx` s volbou `a-2u` si při každém průchodu sám vytváří soubor `pdfa.xmpi` s metadaty PDF/A ve výstupním adresáři; do repozitáře nepatří a nový adresář prezentace jej obsahovat nemusí.
- `assets/theme.tex` — barvy (`maincolor` a od ní odvozené), motiv Beameru, styl bloků, odrážek a záhlaví.
- `assets/macros.tex` — společná makra (viz níže).
- `assets/listing.tex` — styly `listings` pro C (výchozí), Python, C#, Rust; `escapeinside={(*}{*)}`.
- `assets/literatura.bib` — sdílená databáze zdrojů pro všechny prezentace (viz níže).
- `titlepage.tex` — titulní strana. Nezávislá na předmětu: bere údaje z `\title`/`\subtitle`/`\author`/`\email`/`\institute`/`\date` a z `\schoollogo`. Název předmětu lze přepsat `\def\subjectname{...}` **před** vložením souboru.

Změna kteréhokoli souboru v `assets/` nebo `titlepage.tex` se projeví ve všech 25 prezentacích — po zásahu je nutné zkontrolovat víc než jednu.

## Makra, která se používají místo holého Beameru

Definována v `assets/macros.tex`:

- Bloky tvrzení: `defblock`, `thmblock`, `propblock`, `corblock`, `exblock` — volitelný argument je název v závorce (`\begin{defblock}[Ohodnocený graf]`).
- Barevné rámečky: `tnoticebox`/`tinfobox`/`timportantbox`/`talertbox` (s titulkem) a varianty `…frame` (bez titulku). Šířka se **počítá z obsahu** přes `varwidth` + uložené boxy, ručně se nenastavuje; strop je `\linewidth`.
- `\decproblem{Název}{Vstup}{Otázka}` — tabulka rozhodovacího problému.
- `\titleframe{...}` / `titleframeenv` — mezititulní snímek (nezvyšuje číslo snímku), `\tableofcontentsframe` — obsah.
- Automaty: `\state`, `\acceptingstate`, `\initialstate`, `\transitionarrow` (verze s beamer overlay specifikací), TikZ styly `vertex`, `edge`, `diredge`, `state`.
- Matematika: `\R`/`\N`/`\Z`, `\set`, `\mapping`, `\bigO`, operátory tříd složitosti (`\classP`, `\classNP`), `\Astar`.
- Názvy problémů: `\SAT`, `\THREESAT`, `\UNSAT`, `\INDSET` (NzMna), `\CLIQUE`, `\SCHEDULING`, `\SUDOKU`, `\HALT`, `\FACTOR`; nové přes `\newproblem{\MAKRO}{Název}`, jednorázově `\problem{Název}`. Makro rozhodne podle módu: v textu zelené kapitálky (barva `problemfg` z `theme.tex`), v matematice kapitálky písma matematiky se spacingem operátoru (`\mathsc`). Problém zmíněný v textu se proto píše **bez dolarů** (`Problém \SAT{} je …`, za makrem před mezerou `{}`), do matematiky patří jen ve vzorci (`$\INDSET(G,k)=\CLIQUE(\bar{G},k)$`, `$\SAT\in\classNP$`). Číslice v názvu jsou v matematickém módu (`$3$-SAT`). V zápatí a na titulní straně přebírá název barvu okolního textu.
- Zvýrazňování: `\markred`, `\markdarkred`, `\markgreen`, `\markblue`, …; `\cmark`/`\xmark`; `\todo{...}` vysází červenou poznámku do slidu.
- `algorithm2e` je počeštěné (`Vstup`, `Výstup`, `Funkce`) a číslování algoritmů je vypnuté.

Postupné odkrývání se v existujících prezentacích dělá `\visible<n->{...}`, ne `\pause` (kvůli konzistenci sazby mezi standardní a handout variantou).

## Citace a seznam zdrojů

Zdroje se **nepíší ručně do `itemize`**. Všechny jsou v jediné databázi `assets/literatura.bib`, sazbu obstarává `biblatex` se stylem `iso-numeric` (balíček `biblatex-iso690`) podle ČSN ISO 690. Načtení balíčku je v `assets/packages.tex`, barvy a šablona položky v `assets/theme.tex`.

Závěrečný snímek se sází makrem z `assets/macros.tex`:

```latex
\bibframe{mares-valla-labyrint, cormen-algorithms, matousek-diskretni}
\bibframe[Doporučené zdroje]{mares-valla-labyrint, cormen-algorithms}
```

Makro samo vytvoří sekci, provede `\nocite` a vysází `\printbibliography` ve snímku s `allowframebreaks`. Volitelný argument mění název sekce i snímku (výchozí je `Zdroje`). Na zdroj uprostřed výkladu se odkazuje běžným `\cite{klic}`.

Pravidla:

- Nový zdroj patří do `assets/literatura.bib`, ne do konkrétní prezentace. Změna `.bib` se projeví ve všech prezentacích.
- Řazení je `sorting=none`, tedy v pořadí prvního výskytu citace. Pokud je zdroj citován `\cite` uprostřed prezentace, dostane nižší číslo než zdroje uvedené až v `\bibframe`.
- Název s dvojtečkou se zapisuje jako `title` + `subtitle`, ne jako jeden řetězec.
- Po přidání zdroje je nutná plná kompilace (`pdflatex`, `biber`, `pdflatex`, `pdflatex`); `compile.py` ji dělá sám.

## Obrázky

Schémata jsou většinou TikZ zdroje v `ti-NN-*/images/*.tex`, vkládané z `main.tex` přes `\input{images/....tex}`; složitější kresby se vkládají už v preambuli.

Cesty v `\includegraphics` nejsou v repozitáři jednotné: většina prezentací používá `images/soubor.pdf` (relativně k adresáři prezentace), `ti-16-kryptografie` používá plnou cestu `ti-16-kryptografie/images/soubor.pdf`. Při úpravách cest v jedné prezentaci nepřepisuj konvenci ostatních — commit 42036c9 tímhle způsobem rozbil ikony a musel se opravovat.

`.gitignore` ignoruje `*.pdf` (výjimkou je jen `images/SPSE-Jecna_Logo.pdf`). Rastrové a vektorové zdroje ikon jsou proto verzované jako `.svg`/`.png`, ale jejich PDF varianty (`man-icon.pdf`, `woman-icon.pdf`, …) v repozitáři nejsou — musí se vytvořit lokálně, jinak `pdflatex` u dotčených prezentací selže na chybějícím souboru.
