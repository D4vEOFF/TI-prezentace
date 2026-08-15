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

Pro každou variantu kromě té úplně základní skript **vygeneruje dočasnou kopii** `main.tex` (`main_<aspect>[_handout].tex`), v ní regulárním výrazem přepíše volby v řádku `\documentclass` (nahradí `aspectratio=`, přidá/odebere `handout`), spustí `pdflatex` dvakrát, přejmenuje výsledek, dočasný `.tex` smaže a uklidí pomocné soubory (`.aux`, `.nav`, `.snm`, …).

Důsledky pro editaci zdrojů:

- `\documentclass[...]{beamer}` musí zůstat na **jednom řádku**; jinak jej regulární výraz v `update_documentclass_options()` nerozpozná a varianta se vygeneruje beze změny voleb.
- Volbu `handout` nepiš natvrdo do `main.tex` — skript ji u generovaných variant vždy odstraní a doplní podle `--handout`.
- Pokud kompilace spadne uprostřed, může v adresáři zůstat dočasný `main_*.tex` (v `ti-00-informace/` takový zbytek je). Do commitu nepatří.

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

- `assets/packages.tex` — balíčky. Pozor na `pdfx` s volbou `a-2u`: vyžaduje v adresáři prezentace soubor `pdfa.xmpi` s metadaty PDF/A. Nový adresář prezentace musí `pdfa.xmpi` obsahovat, jinak kompilace selže.
- `assets/theme.tex` — barvy (`maincolor` a od ní odvozené), motiv Beameru, styl bloků, odrážek a záhlaví.
- `assets/macros.tex` — společná makra (viz níže).
- `assets/listing.tex` — styly `listings` pro C (výchozí), Python, C#, Rust; `escapeinside={(*}{*)}`.
- `titlepage.tex` — titulní strana. Nezávislá na předmětu: bere údaje z `\title`/`\subtitle`/`\author`/`\email`/`\institute`/`\date` a z `\schoollogo`. Název předmětu lze přepsat `\def\subjectname{...}` **před** vložením souboru.

Změna kteréhokoli souboru v `assets/` nebo `titlepage.tex` se projeví ve všech 25 prezentacích — po zásahu je nutné zkontrolovat víc než jednu.

## Makra, která se používají místo holého Beameru

Definována v `assets/macros.tex`:

- Bloky tvrzení: `defblock`, `thmblock`, `propblock`, `corblock`, `exblock` — volitelný argument je název v závorce (`\begin{defblock}[Ohodnocený graf]`).
- Barevné rámečky: `tnoticebox`/`tinfobox`/`timportantbox`/`talertbox` (s titulkem) a varianty `…frame` (bez titulku). Šířka se **počítá z obsahu** přes `varwidth` + uložené boxy, ručně se nenastavuje; strop je `\linewidth`.
- `\decproblem{Název}{Vstup}{Otázka}` — tabulka rozhodovacího problému.
- `\titleframe{...}` / `titleframeenv` — mezititulní snímek (nezvyšuje číslo snímku), `\tableofcontentsframe` — obsah.
- Automaty: `\state`, `\acceptingstate`, `\initialstate`, `\transitionarrow` (verze s beamer overlay specifikací), TikZ styly `vertex`, `edge`, `diredge`, `state`.
- Matematika: `\R`/`\N`/`\Z`, `\set`, `\mapping`, `\bigO`, operátory tříd složitosti (`\classP`, `\classNP`) a problémů (`\SAT`, `\THREESAT`, `\NZMNA`, `\KLIKA`), `\Astar`.
- Zvýrazňování: `\markred`, `\markdarkred`, `\markgreen`, `\markblue`, …; `\cmark`/`\xmark`; `\todo{...}` vysází červenou poznámku do slidu.
- `algorithm2e` je počeštěné (`Vstup`, `Výstup`, `Funkce`) a číslování algoritmů je vypnuté.

Postupné odkrývání se v existujících prezentacích dělá `\visible<n->{...}`, ne `\pause` (kvůli konzistenci sazby mezi standardní a handout variantou).

## Obrázky

Schémata jsou většinou TikZ zdroje v `ti-NN-*/images/*.tex`, vkládané z `main.tex` přes `\input{images/....tex}`; složitější kresby se vkládají už v preambuli.

Cesty v `\includegraphics` nejsou v repozitáři jednotné: většina prezentací používá `images/soubor.pdf` (relativně k adresáři prezentace), `ti-16-kryptografie` používá plnou cestu `ti-16-kryptografie/images/soubor.pdf`. Při úpravách cest v jedné prezentaci nepřepisuj konvenci ostatních — commit 42036c9 tímhle způsobem rozbil ikony a musel se opravovat.

`.gitignore` ignoruje `*.pdf` (výjimkou je jen `images/SPSE-Jecna_Logo.pdf`). Rastrové a vektorové zdroje ikon jsou proto verzované jako `.svg`/`.png`, ale jejich PDF varianty (`man-icon.pdf`, `woman-icon.pdf`, …) v repozitáři nejsou — musí se vytvořit lokálně, jinak `pdflatex` u dotčených prezentací selže na chybějícím souboru.
