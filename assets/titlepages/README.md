# Návrhy titulní strany

Adresář obsahuje návrhy nové titulní strany prezentací. Cílem je vzhled, který

- zachovává všechny dosavadní údaje (název předmětu, téma přednášky, autor, e-mail, škola, logo školy, školní rok),
- drží současnou barevnost (hlavní barva `maincolor`, tj. `#8B00B5`, a světlejší doplňková `titlefooterbg`),
- není vázaný na předmět, takže jej lze beze změny použít i pro matematiku, informatiku a další předměty.

## Náhled

Náhledový dokument [`nahled-titulnich-stran/main.tex`](../../nahled-titulnich-stran/main.tex) sází každou variantu dvakrát: jednou s předmětem *Teoretická informatika* a nejdelším reálným názvem tématu, podruhé s předmětem *Matematika*. Zkompiluje se příkazem:

```bash
python compile.py -f nahled-titulnich-stran -t nahled -ar 43 1610
```

Vzniknou soubory `nahled_43.pdf` a `nahled_1610.pdf`.

## Varianty

| Soubor | Varianta | Popis |
|---|---|---|
| [`varianta-0-soucasna.tex`](varianta-0-soucasna.tex) | 0 – současný stav | Dnešní titulní strana, ponechaná pro porovnání. |
| [`varianta-1-bocni-pruh.tex`](varianta-1-bocni-pruh.tex) | 1 – boční pruh | Svislý pruh v hlavní barvě u levého okraje s názvem předmětu, ostatní údaje vpravo. |
| [`varianta-2-zahlavi.tex`](varianta-2-zahlavi.tex) | 2 – barevné záhlaví | Horní polovina strany v barevném přechodu, údaje o autorovi dole. |
| [`varianta-3-karta.tex`](varianta-3-karta.tex) | 3 – karta se stínem | Evoluce současného řešení: karta se stínem, barevná hlavička se jménem předmětu a školním rokem. |
| [`varianta-4-minimal.tex`](varianta-4-minimal.tex) | 4 – minimalistická | Světlý podklad, svislá linka u textu, decentní bodová mřížka v rohu. |
| [`varianta-5-diagonala.tex`](varianta-5-diagonala.tex) | 5 – diagonála | Šikmé rozdělení strany na barevnou a světlou část. |

Soubor [`spolecne.tex`](spolecne.tex) obsahuje pomůcky sdílené všemi variantami (vypnutí dělení slov v názvu tématu, barva školního roku, sazba textu na barevném podkladu).

## Použití pro jiný předmět

Šablony berou údaje výhradně z příkazů Beameru, žádný text v nich není napevno:

| Údaj | Zdroj |
|---|---|
| Název předmětu | `\title` (v `titlepage.tex` z makra `\subjectname`) |
| Téma přednášky | `\subtitle` (z makra `\presentationtitle`) |
| Autor | `\author` |
| E-mail | `\email` |
| Škola | `\institute` |
| Školní rok | `\date` |
| Logo školy | `\schoollogo` |

Předmět se v konkrétní prezentaci změní zápisem před vložením `titlepage.tex`:

```latex
\def\subjectname{Matematika}
\def\presentationtitle{Derivace a~její geometrický význam}
```

Bez tohoto zápisu se použije výchozí hodnota `Teoretická informatika`.

## Zavedení vybrané varianty

Po výběru varianty stačí:

1. v `assets/theme.tex` nahradit stávající definici šablony `title page` obsahem vybraného souboru,
2. načíst `assets/titlepages/spolecne.tex` (nebo jeho obsah přenést do `assets/macros.tex`),
3. odstranit tento adresář s návrhy i adresář `nahled-titulnich-stran/`,
4. znovu zkompilovat všechny prezentace ve všech používaných poměrech stran.

## Poznámky

- Šablony kreslí přes celou stranu pomocí TikZ (`remember picture, overlay`), proto je nutné `pdflatex` spustit dvakrát. Skript `compile.py` to dělá automaticky.
- Varianty byly ověřeny v poměrech stran 4:3 a 16:10, včetně nejdelšího názvu tématu, který se v repozitáři vyskytuje.
- Makro `\Astar` sází v základní podobě „A*“ napevno černě. Na barevném podkladu je proto v šablonách dočasně předefinováno na variantu dědící barvu okolního textu (viz `\tpinverse` ve `spolecne.tex`).
- Čísla školního roku vznikají v matematickém režimu, takže se jim barva nastavuje zvlášť (makro `\tpdate`).
