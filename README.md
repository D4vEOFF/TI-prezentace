<img src="https://www.spsejecna.cz/ci/SPSE-Jecna_Logotyp.svg">

# Materiály pro předmět Teoretická informatika (TI)

Repozitář obsahuje zdrojové soubory výukových prezentací k předmětu **Teoretická informatika** na SPŠE Ječná. Materiály jsou vytvořeny v systému LaTeX pomocí třídy Beamer.

Hlavní série zahrnuje 22 prezentací označených čísly `00` až `21`. Pokrývá grafové algoritmy, výpočetní složitost, formální jazyky a automaty, kompilátory, hardware, kryptografii, statistiku, strojové učení a neuronové sítě.

Repozitář obsahuje zdrojové soubory prezentací. Výsledná PDF lze vytvořit pomocí skriptu [`compile.py`](compile.py).

## Obsah

- [Materiály pro předmět Teoretická informatika (TI)](#materiály-pro-předmět-teoretická-informatika-ti)
  - [Obsah](#obsah)
  - [Struktura repozitáře](#struktura-repozitáře)
  - [Požadavky](#požadavky)
  - [Kompilace prezentací](#kompilace-prezentací)
    - [Kompilace jedné prezentace](#kompilace-jedné-prezentace)
    - [Volba poměru stran](#volba-poměru-stran)
    - [Vytvoření handoutu](#vytvoření-handoutu)
    - [Kompilace všech prezentací](#kompilace-všech-prezentací)
    - [Parametry skriptu](#parametry-skriptu)
    - [Názvy výstupních souborů](#názvy-výstupních-souborů)
  - [Obsah jednotlivých prezentací](#obsah-jednotlivých-prezentací)
    - [Informace k předmětu](#informace-k-předmětu)
      - [00 – Informace k předmětu](#00--informace-k-předmětu)
    - [Grafové algoritmy](#grafové-algoritmy)
      - [01 – Opakování z teorie grafů](#01--opakování-z-teorie-grafů)
      - [02 – Algoritmy BFS a DFS](#02--algoritmy-bfs-a-dfs)
      - [03 – Binární halda](#03--binární-halda)
      - [04 – Dijkstrův algoritmus](#04--dijkstrův-algoritmus)
      - [05 – Algoritmus A\*](#05--algoritmus-a)
    - [Algoritmicky těžké problémy](#algoritmicky-těžké-problémy)
      - [06 – Úvod do algoritmicky těžkých problémů](#06--úvod-do-algoritmicky-těžkých-problémů)
      - [07 – Problémy SAT a UNSAT](#07--problémy-sat-a-unsat)
      - [08 – Algoritmus DPLL](#08--algoritmus-dpll)
      - [09 – Problémy 3-SAT, nezávislé množiny a kliky](#09--problémy-3-sat-nezávislé-množiny-a-kliky)
      - [10 – Třídy problémů P a NP](#10--třídy-problémů-p-a-np)
    - [Formální jazyky, automaty a kompilátory](#formální-jazyky-automaty-a-kompilátory)
      - [11 – Konečné automaty](#11--konečné-automaty)
      - [12 – Regulární výrazy](#12--regulární-výrazy)
      - [13 – Formální gramatiky](#13--formální-gramatiky)
      - [14 – Kompilátory](#14--kompilátory)
    - [Počítačový hardware](#počítačový-hardware)
      - [15 – Rychlý přehled hardwaru](#15--rychlý-přehled-hardwaru)
    - [Kryptografie](#kryptografie)
      - [16 – Kryptografie](#16--kryptografie)
    - [Umělá inteligence a strojové učení](#umělá-inteligence-a-strojové-učení)
      - [17 – Statistické pojmy](#17--statistické-pojmy)
      - [18 – Strojové učení](#18--strojové-učení)
      - [19 – Lineární regrese](#19--lineární-regrese)
      - [20 – Klasifikace](#20--klasifikace)
      - [21 – Neuronové sítě](#21--neuronové-sítě)
  - [Úprava prezentací](#úprava-prezentací)
  - [Autor a licence](#autor-a-licence)
  - [Použitá a doporučená literatura](#použitá-a-doporučená-literatura)

## Struktura repozitáře

```text
TI-prezentace/
├── assets/
│   ├── listing.tex
│   ├── macros.tex
│   ├── packages.tex
│   └── theme.tex
├── images/
│   └── SPSE-Jecna_Logo.pdf
├── ti-00-informace/
│   └── main.tex
├── ti-01-teorie-grafu-opakovani/
│   ├── images/
│   └── main.tex
├── ...
├── ti-21-neuronove-site/
│   ├── images/
│   └── main.tex
├── ti-99-*/
├── compile.py
└── titlepage.tex
```

Jednotlivé části mají následující význam:

- `assets/packages.tex` načítá společné balíčky LaTeXu;
- `assets/theme.tex` definuje vzhled prezentací, barvy a nastavení Beameru;
- `assets/macros.tex` obsahuje společná matematická, grafická a typografická makra;
- `assets/listing.tex` obsahuje nastavení výpisů zdrojového kódu;
- `images/` obsahuje společné obrázky, zejména logo školy;
- `titlepage.tex` definuje společnou titulní stranu, která není vázaná na konkrétní předmět;
- `ti-NN-nazev/` obsahuje zdrojové soubory příslušné prezentace;
- `compile.py` zajišťuje kompilaci prezentací, tvorbu různých poměrů stran a handoutů.

Hlavním souborem každé prezentace je `main.tex`. Některé prezentace obsahují také další soubory s pseudokódy, zdrojovými kódy nebo obrázky vytvořenými v TikZ.

## Požadavky

Pro kompilaci prezentací jsou potřeba:

- **Python 3**;
- distribuce LaTeXu obsahující program `pdflatex`, například
  - TeX Live nebo
  - MiKTeX;
- česká jazyková podpora pro balíček `babel`;
- balíčky LaTeXu uvedené v souboru [`assets/packages.tex`](assets/packages.tex).

Projekt používá mimo jiné balíčky Beamer, TikZ, PGFPlots, `algorithm2e`, `tcolorbox`, `listings`, `pdfx`, `mathtools`, `subcaption`, `tabularx` a `makecell`. Vzhledem k většímu množství závislostí je vhodná úplná instalace TeX Live nebo MiKTeXu.

Dostupnost potřebných programů lze ověřit příkazy:

```bash
python --version
pdflatex --version
```

Na některých systémech je nutné místo příkazu `python` použít `python3`.

## Kompilace prezentací

Skript [`compile.py`](compile.py):

- vyhledá příslušný soubor `main.tex`;
- podle zadaných parametrů vytvoří požadovanou variantu prezentace;
- spustí `pdflatex` dvakrát;
- přejmenuje výsledné PDF;
- odstraní dočasné zdrojové a pomocné soubory.

Příkazy v následujících příkladech se spouštějí z kořenového adresáře repozitáře.

### Kompilace jedné prezentace

Při kompilaci jedné prezentace je třeba zadat její adresář a název výsledného souboru:

```bash
python compile.py \
    -f ti-01-teorie-grafu-opakovani \
    -t ti-01-teorie-grafu-opakovani
```

Výsledkem bude soubor:

```text
ti-01-teorie-grafu-opakovani/ti-01-teorie-grafu-opakovani.pdf
```

Není-li zadán poměr stran, použije se poměr uvedený v původním souboru `main.tex`. V současných prezentacích je výchozím poměrem stran `4:3`.

### Volba poměru stran

Poměry stran se zadávají parametrem `-ar`, `-ars` nebo `--aspect-ratios`:

```bash
python compile.py \
    -f ti-01-teorie-grafu-opakovani \
    -t ti-01-teorie-grafu-opakovani \
    -ar 43 169 1610
```

Tím se vytvoří soubory:

```text
ti-01-teorie-grafu-opakovani_43.pdf
ti-01-teorie-grafu-opakovani_169.pdf
ti-01-teorie-grafu-opakovani_1610.pdf
```

Poměry lze zapisovat také s oddělovačem:

```bash
-ar 4:3 16:9 16:10
```

Skript tyto zápisy automaticky převede na hodnoty používané třídou Beamer:

| Zápis | Normalizovaná hodnota | Poměr stran |
|---|---:|---:|
| `43` nebo `4:3` | `43` | 4:3 |
| `169` nebo `16:9` | `169` | 16:9 |
| `1610` nebo `16:10` | `1610` | 16:10 |

### Vytvoření handoutu

Parametr `--handout` vytvoří vedle standardní prezentace také variantu s volbou `handout` třídy Beamer:

```bash
python compile.py \
    -f ti-01-teorie-grafu-opakovani \
    -t ti-01-teorie-grafu-opakovani \
    --handout \
    -ar 43 169
```

Výsledkem budou soubory:

```text
ti-01-teorie-grafu-opakovani_43.pdf
ti-01-teorie-grafu-opakovani_43_handout.pdf
ti-01-teorie-grafu-opakovani_169.pdf
ti-01-teorie-grafu-opakovani_169_handout.pdf
```

Handout obsahuje všechny části jednotlivých slidů současně a nepracuje s postupným odkrýváním obsahu.

### Kompilace všech prezentací

Parametr `--all` vyhledá všechny podadresáře obsahující soubor `main.tex`:

```bash
python compile.py --all -ar 43 169 1610
```

Název výstupního souboru se v tomto případě odvodí od názvu adresáře prezentace.

Všechny prezentace včetně handoutů lze vytvořit příkazem:

```bash
python compile.py --all --handout -ar 43 169 1610
```

Parametr `--move` přesune vytvořená PDF z adresářů prezentací do adresáře, ze kterého byl skript spuštěn:

```bash
python compile.py --all --handout --move -ar 43 169 1610
```

> [!NOTE]
> Parametr `--all` zpracuje každý podadresář obsahující `main.tex`. Zahrne proto také doplňkové a rozpracované materiály označené číslem `99`.

### Parametry skriptu

| Parametr | Význam |
|---|---|
| `-f`, `--folder` | Adresář obsahující kompilovaný soubor `main.tex`. |
| `-t`, `--title` | Název výsledného PDF bez přípony `.pdf`. |
| `--all` | Zkompiluje všechny podadresáře obsahující `main.tex`. |
| `--handout` | Vytvoří také handout pro každý požadovaný poměr stran. |
| `-ar`, `-ars`, `--aspect-ratios` | Určuje jeden nebo více poměrů stran. |
| `--move` | Přesune všechna vytvořená PDF do aktuálního adresáře. |
| `-h`, `--help` | Vypíše nápovědu skriptu. |

Parametry `--folder` a `--title` jsou povinné, pokud není použit parametr `--all`.

### Názvy výstupních souborů

Pro název zadaný parametrem `--title prezentace` používá skript následující schéma:

| Varianta | Název souboru |
|---|---|
| Výchozí varianta | `prezentace.pdf` |
| Výchozí handout | `prezentace_handout.pdf` |
| Poměr stran 4:3 | `prezentace_43.pdf` |
| Handout 4:3 | `prezentace_43_handout.pdf` |
| Poměr stran 16:9 | `prezentace_169.pdf` |
| Handout 16:9 | `prezentace_169_handout.pdf` |
| Poměr stran 16:10 | `prezentace_1610.pdf` |
| Handout 16:10 | `prezentace_1610_handout.pdf` |

## Obsah jednotlivých prezentací

### Informace k předmětu

#### [00 – Informace k předmětu](ti-00-informace/main.tex)

Úvodní prezentace seznamuje žáky s organizací předmětu, způsobem hodnocení a tematickými výstupy, které budou v průběhu školního roku postupně zpracovávat. Vysvětluje, co mohou jednotlivé výstupy obsahovat, jakým způsobem se budou odevzdávat a jaké podmínky je třeba splnit pro uzavření klasifikace.

Druhá část poskytuje přehled celého sylabu. Představuje tematické celky věnované grafovým algoritmům, algoritmicky těžkým problémům, konečným automatům, hardwaru, kompilátorům, kryptografii a umělé inteligenci. Na závěr uvádí základní doporučenou literaturu využitelnou při studiu jednotlivých témat.

### Grafové algoritmy

#### [01 – Opakování z teorie grafů](ti-01-teorie-grafu-opakovani/main.tex)

Prezentace opakuje základní pojmy z teorie grafů a ukazuje, kde se s grafy setkáváme v informatice i v běžném životě. Zavádí graf, vrcholy, hrany, cesty a vzdálenosti a následně porovnává nejběžnější způsoby reprezentace grafů: matici sousednosti, matici incidence a seznamy sousedů. U každé reprezentace se zabývá jejími vlastnostmi a paměťovou náročností.

Další část je věnována stupni vrcholu, principu sudosti a časové složitosti základních operací nad jednotlivými reprezentacemi grafu. Závěr připomíná souvislé grafy a stromy a uvádí několik vzájemně ekvivalentních charakterizací stromu.

#### [02 – Algoritmy BFS a DFS](ti-02-bfs-dfs/main.tex)

Prezentace podrobně vysvětluje dva základní algoritmy pro prohledávání grafů. Nejprve představuje prohledávání do šířky BFS, jeho postup, pseudokód a implementaci v Pythonu. Na konkrétních příkladech ukazuje rozdělení vrcholů do vrstev, výpočet vzdáleností od počátečního vrcholu a konstrukci stromu nejkratších cest. Součástí je také rozbor časové a prostorové složitosti algoritmu.

Druhá část obdobným způsobem probírá prohledávání do hloubky DFS. Vedle postupu, pseudokódu a implementace se věnuje časům vstupu a výstupu jednotlivých vrcholů a vztahům mezi intervaly určenými těmito časy. Získané vlastnosti jsou následně využity při vysvětlení algoritmu pro hledání mostů v grafu.

#### [03 – Binární halda](ti-03-halda/main.tex)

Prezentace nejprve opakuje binární stromy a jejich hladiny a následně zavádí minimovou a maximovou binární haldu. Vysvětluje tvarovou podmínku haldy i podmínku určující uspořádání hodnot mezi rodičem a jeho potomky. Na konkrétních příkladech ukazuje, které stromy podmínky binární haldy splňují a které nikoliv.

Hlavní část je věnována operacím `Insert`, `BubbleUp`, `ExtractMin` a `BubbleDown`. Prezentace znázorňuje jednotlivé kroky těchto operací, uvádí jejich pseudokódy a odvozuje jejich časovou složitost z počtu hladin stromu. Dále vysvětluje reprezentaci haldy pomocí pole, vztahy mezi indexy rodiče a potomků a doplňkové operace `Increase` a `Decrease`.

#### [04 – Dijkstrův algoritmus](ti-04-dijkstra/main.tex)

Prezentace zavádí ohodnocené grafy, délku cesty a vzdálenost vrcholů v ohodnoceném grafu. Vysvětluje problém hledání nejkratších cest a upozorňuje na význam znamének vah hran. Na tuto motivaci navazuje formulací základní myšlenky Dijkstrova algoritmu a podrobným průchodem algoritmu na konkrétním příkladu.

Vedle samotného postupu se prezentace věnuje také správnosti algoritmu a podmínkám, za kterých lze Dijkstrův algoritmus použít. V závěru porovnává jeho implementaci s využitím pole a binární haldy a ukazuje, jak volba datové struktury ovlivňuje výslednou časovou složitost.

#### [05 – Algoritmus A*](ti-05-a-star/main.tex)

Prezentace navazuje na problematiku hledání nejkratších cest a ukazuje, jak lze prohledávání urychlit pomocí dodatečné informace o odhadované vzdálenosti k cíli. Zavádí heuristickou funkci, vysvětluje její význam a uvádí typické příklady, zejména eukleidovskou a manhattanskou vzdálenost. Zabývá se také požadavky kladenými na heuristiku, především její přípustností a konzistencí.

Následně představuje algoritmus A*, jeho hodnoticí funkci, postup a pseudokód. Chování algoritmu je ilustrováno jak při hledání cesty v bludišti, tak na obecném ohodnoceném grafu. Závěrečná část vysvětluje, proč algoritmus při splnění příslušných podmínek nalezne nejkratší cestu.

### Algoritmicky těžké problémy

#### [06 – Úvod do algoritmicky těžkých problémů](ti-06-algoritmicky-tezke-problemy/main.tex)

Prezentace otevírá problematiku úloh, pro které neznáme dostatečně rychlé algoritmy, případně které nelze algoritmicky vyřešit vůbec. Přechází od neformálního vnímání obtížnosti k formálnímu pojetí výpočetního problému a vysvětluje, proč se při rozlišování prakticky zvládnutelných a nezvládnutelných výpočtů používá pojem polynomiálního času.

Rozdíl mezi rychle rostoucí časovou složitostí a principiální neřešitelností je ukázán na Hanojských věžích a problému zastavení. Hanojské věže slouží také k vysvětlení převodu původního problému na rozhodovací variantu. Problém zastavení následně představuje příklad problému, pro který nemůže existovat algoritmus řešící všechny možné vstupy.

#### [07 – Problémy SAT a UNSAT](ti-07-sat-unsat/main.tex)

Prezentace nejprve opakuje výrokovou logiku, základní logické operace, pravdivostní tabulky a důležité ekvivalence mezi logickými formulemi. Poté zavádí literály, klauzule a konjunktivní normální formu. Ukazuje převod formule do CNF pomocí pravdivostní tabulky a vysvětluje také princip Tseitinovy transformace, která umožňuje omezit velikost výsledné formule.

Na tomto základě jsou formálně zavedeny problémy SAT a UNSAT. Prezentace objasňuje rozdíl mezi hledáním splňujícího ohodnocení a dokazováním nesplnitelnosti formule a vysvětluje, proč má problém SAT zásadní význam v teorii výpočetní složitosti i v praktických aplikacích.

#### [08 – Algoritmus DPLL](ti-08-dpll/main.tex)

Prezentace navazuje na problém SAT a představuje algoritmus DPLL pro rozhodování splnitelnosti formulí v konjunktivní normální formě. Nejprve zavádí jednotkové klauzule, polaritu literálu a čisté literály. Poté vysvětluje tři hlavní mechanismy algoritmu: jednotkovou propagaci, eliminaci čistých literálů a větvení podle zvoleného literálu.

Průběh algoritmu je znázorněn pomocí stavového schématu i konkrétního příkladu. Součástí prezentace je rovněž pseudokód zachycující rekurzivní strukturu DPLL a rozbor jeho časové složitosti. Ten ukazuje, že algoritmus může v nejhorším případě projít exponenciálně mnoho různých ohodnocení.

#### [09 – Problémy 3-SAT, nezávislé množiny a kliky](ti-09-3sat-nzmna-klika/main.tex)

Prezentace zavádí problém 3-SAT a pojem polynomiální převoditelnosti výpočetních problémů. Vysvětluje, co převod mezi problémy znamená, jakým směrem se při posuzování obtížnosti používá a jak lze pomocí převodu přenášet řešitelnost nebo obtížnost jednoho problému na jiný. Samostatná část se věnuje vztahu mezi problémy SAT a 3-SAT.

Dále jsou představeny problémy nezávislé množiny a kliky v grafu. Prezentace rozlišuje jejich optimalizační a rozhodovací formulace, ukazuje převod problému 3-SAT na problém nezávislé množiny a vysvětluje vztah mezi nezávislou množinou a klikou prostřednictvím doplňku grafu. Závěr shrnuje síť převodů mezi probíranými problémy.

#### [10 – Třídy problémů P a NP](ti-10-p-np/main.tex)

Prezentace nejprve vysvětluje rozdíl mezi optimalizačními a rozhodovacími problémy a důvod, proč se teorie výpočetní složitosti často soustředí právě na rozhodovací varianty. Následně zavádí třídu P jako množinu problémů řešitelných v polynomiálním čase a třídu NP prostřednictvím polynomiálně ověřitelných certifikátů. Zařazení problémů do NP je ilustrováno na Sudoku, SAT, nezávislé množině, klice a dalších problémech.

Druhá část se věnuje vztahu tříd P a NP a pojmu NP-úplného problému. Formuluje Cookovu–Levinovu větu, ukazuje princip převodu Sudoku na SAT a vysvětluje, jak se polynomiální převody používají k dokazování NP-úplnosti. Závěr shrnuje důsledky případného nalezení polynomiálního algoritmu pro jediný NP-úplný problém.

### Formální jazyky, automaty a kompilátory

#### [11 – Konečné automaty](ti-11-det-nedet-automaty/main.tex)

Prezentace uvádí konečné automaty jako jednoduché matematické modely výpočtu. Nejprve zavádí abecedu, slovo a formální jazyk, připomíná základní operace nad slovy a vysvětluje vztah mezi rozhodovacím problémem a jazykem. Poté formálně popisuje deterministický konečný automat, jeho přechodovou funkci, počáteční stav, přijímající stavy a průběh výpočtu nad vstupním slovem.

Následně představuje nedeterministické konečné automaty a ilustruje jejich použití například při hledání podslova. Vysvětluje význam nedeterministického větvení a vztah mezi výpočetní silou DFA a NFA. Závěrečná část zavádí regulární jazyky a na příkladech ukazuje, které jazyky lze konečným automatem rozpoznat a jak lze dokazovat, že pro určitý jazyk žádný konečný automat neexistuje.

#### [12 – Regulární výrazy](ti-12-regex/main.tex)

Prezentace navazuje na konečné automaty a zavádí regulární výrazy jako druhý způsob popisu regulárních jazyků. Formálně vysvětluje základní regulární výrazy a operace sjednocení, zřetězení a iterace. Jejich význam ukazuje na konkrétních příkladech jazyků nad různými abecedami.

Ústředním výsledkem prezentace je Kleeneho věta, podle níž regulární výrazy a konečné automaty popisují právě tutéž třídu jazyků. Vedle formulace věty je uveden také náznak obou směrů jejího důkazu. Závěr obsahuje další příklady regulárních výrazů a ukazuje rozdíl mezi jejich formálním pojetím a rozšířenou syntaxí používanou v programovacích jazycích a praktických nástrojích.

#### [13 – Formální gramatiky](ti-13-gramatiky/main.tex)

Prezentace představuje formální gramatiky jako prostředek pro generování slov a jazyků. Po krátké rekapitulaci formálních jazyků vysvětluje motivaci jejich použití a zavádí gramatiku pomocí množiny terminálů, množiny neterminálů, počátečního symbolu a přepisovacích pravidel. Následně definuje derivaci a jazyk generovaný gramatikou a ukazuje jejich použití na konkrétních příkladech.

Pozornost je věnována také souvislosti mezi formálními gramatikami a přirozeným jazykem. Závěrečná část se zaměřuje na regulární gramatiky, jejich omezený tvar přepisovacích pravidel a vztah k regulárním jazykům a konečným automatům.

#### [14 – Kompilátory](ti-14-kompilatory/main.tex)

Prezentace vysvětluje cestu od zdrojového kódu ke spustitelnému programu a rozlišuje zdrojový jazyk, mezikód a strojový kód. Představuje základní fáze překladače a podrobněji se věnuje lexikální analýze, při níž jsou znaky vstupu seskupovány do lexémů a převáděny na tokeny. Na ni navazuje syntaktická analýza, bezkontextové gramatiky, derivační stromy a zpracování aritmetických výrazů. Porovnány jsou také základní principy syntaktické analýzy shora dolů a zdola nahoru.

Další část se zabývá sémantickou analýzou a optimalizací výsledného programu. Rozlišuje lokální a globální optimalizace a uvádí příklady, jako jsou vyhodnocení konstantních výrazů, odstranění mrtvého kódu a eliminace společných podvýrazů. Závěr porovnává kompilované a interpretované jazyky, vysvětluje činnost interpretu, příčiny nižší rychlosti interpretovaných programů a princip JIT kompilace.

### Počítačový hardware

#### [15 – Rychlý přehled hardwaru](ti-15-hardware/main.tex)

Prezentace poskytuje základní přehled fyzických částí počítače a jejich vzájemné spolupráce. Vysvětluje úlohu procesoru, operační paměti, vstupních a výstupních zařízení a externích pamětí. Samostatná část je věnována von Neumannově architektuře a jejímu porovnání s harvardskou architekturou.

Podrobněji prezentace rozebírá části procesoru, instrukční cyklus a význam registrů a vyrovnávací paměti. Dále popisuje organizaci operační paměti, princip SSD a HDD, vnitřní strukturu pevného disku a uložení dat na jeho plotnách. Jednotlivé druhy pamětí jsou nakonec uspořádány do paměťové hierarchie podle rychlosti, kapacity, ceny a vzdálenosti od procesoru.

### Kryptografie

#### [16 – Kryptografie](ti-16-kryptografie/main.tex)

Prezentace nejprve zavádí základní kryptologické pojmy a obecný komunikační model zahrnující otevřený text, šifrový text, šifrovací a dešifrovací algoritmus a útočníka. Historický vývoj šifrování ukazuje na substitučních metodách. Následně přechází k symetrické kryptografii, formálně popisuje šifrovací schéma a bezpečnostní vlastnosti perfektního šifrování a podrobněji se věnuje jednorázové šifře. Na symetrické metody navazuje princip asymetrické kryptografie a práce s veřejným a soukromým klíčem.

Samostatný rozsáhlý celek je věnován algoritmu RSA, jeho matematickým základům, korektnosti a bezpečnosti. Další části zavádějí pseudonáhodné generátory, výpočetní nerozlišitelnost a jednosměrné funkce a vysvětlují jejich vztah ke kryptografii. Prezentace se dále zabývá hešovacími funkcemi, narozeninovým paradoxem, hledáním kolizí, bezpečnostními vlastnostmi hešovacích funkcí a rodinou SHA se zaměřením na sponge konstrukci a SHA-3. Závěr představuje elektronický podpis, jeho základní princip, praktické využití a právní rámec.

### Umělá inteligence a strojové učení

#### [17 – Statistické pojmy](ti-17-statistika/main.tex)

Prezentace buduje statistický základ potřebný pro další témata strojového učení. Nejprve vysvětluje rozdíl mezi samotnými daty a informací získanou jejich interpretací a zavádí statistický soubor, statistickou jednotku a statistický znak. Poté probírá charakteristiky polohy: aritmetický průměr, jeho vlastnosti, vážený průměr a medián. Na ně navazují charakteristiky variability, zejména rozptyl a směrodatná odchylka.

Další část se věnuje standardizaci a min-max normalizaci dat a změnám, které tyto transformace způsobují. Při zkoumání vztahu dvou statistických znaků jsou zavedeny kovariance a korelační koeficient včetně jejich vlastností a interpretace. Prezentace zároveň upozorňuje na omezení korelace, možnost nelineárních závislostí, vliv odlehlých hodnot a zásadní rozdíl mezi korelací a kauzalitou.

#### [18 – Strojové učení](ti-18-strojove-uceni/main.tex)

Prezentace nejprve vymezuje umělou inteligenci a ukazuje různé způsoby, jak lze inteligentní chování strojů chápat. Představuje Turingův test a model inteligentního agenta, který vnímá prostředí, volí akce a sleduje určitý cíl. Poté zavádí strojové učení jako oblast, v níž se model učí z dat. Vysvětluje význam trénovacích a testovacích dat, proces trénování a následné vyhodnocení naučeného modelu.

Hlavní část rozděluje strojové učení na učení s učitelem, učení bez učitele a zpětnovazební učení. U učení s učitelem rozlišuje regresi a klasifikaci a stručně představuje lineární regresi. Učení bez učitele ilustruje na shlukové analýze a algoritmu k-means. V části věnované zpětnovazebnímu učení zavádí agenta, prostředí, stavy, akce, odměny a politiku a na jednoduchém příkladu vysvětluje základní princip algoritmu Q-learning.

#### [19 – Lineární regrese](ti-19-linearni-regrese/main.tex)

Prezentace podrobně představuje lineární regresi jako metodu pro popis a předpovídání lineární závislosti mezi dvěma veličinami. Zavádí regresní přímku, predikované hodnoty a rezidua a ukazuje, jak lze kvalitu modelu měřit pomocí součtu čtvercových chyb a střední kvadratické chyby. Metoda nejmenších čtverců je použita k odvození parametrů nejlepší regresní přímky.

Další část zkoumá vztah směrnice regresní přímky, směrodatných odchylek a korelačního koeficientu. Vysvětluje také, proč je po standardizaci směrnice regresní přímky rovna korelaci. Následně zavádí koeficient determinace, ukazuje jeho výpočet na konkrétních datech a vysvětluje jeho interpretaci. Závěr upozorňuje na předpoklady a omezení lineárního modelu, odlehlé hodnoty, nelineární závislosti a nebezpečí extrapolace.

#### [20 – Klasifikace](ti-20-klasifikace/main.tex)

Prezentace zavádí klasifikaci jako úlohu přiřazování objektů do předem určených tříd. Na motivačních příkladech vysvětluje vstupní příznaky, třídy, skóre klasifikátoru a rozhodovací pravidlo a rozlišuje binární, vícetřídní a víceznačkovou klasifikaci. První probíranou metodou je logistická regrese. Prezentace ukazuje, proč pro klasifikaci nestačí běžná lineární regrese, zavádí logistickou funkci, rozhodovací práh a křížovou entropii a popisuje proces trénování logistického modelu.

Druhá část se zaměřuje na vyhodnocení klasifikace. Rozlišuje správné a chybné klasifikace a zavádí správnost, přesnost, pokrytí a F-míru. Ukazuje, jak se jednotlivé metriky doplňují, jak je ovlivňuje rozhodovací práh a proč je nutné model ověřovat na datech, která nebyla použita při jeho trénování. Závěr představuje algoritmus k-NN, volbu parametru \(k\), význam vzdálenosti mezi objekty a hlavní výhody i omezení této metody.

#### [21 – Neuronové sítě](ti-21-neuronove-site/main.tex)

Prezentace začíná biologickou inspirací neuronových sítí a postupně přechází od biologického neuronu k jeho formálnímu modelu. Zavádí vstupy, váhy, prahovou hodnotu a přenosovou funkci a popisuje neuronovou síť jako orientovaný graf. Následně vysvětluje dopředné neuronové sítě, perceptron, jeho výpočet a geometrickou interpretaci a porovnává skokovou funkci, sigmoidu a další přenosové funkce. Na perceptron navazuje vícevrstvý perceptron a výpočet hodnot v jednotlivých vrstvách.

Část věnovaná učení neuronových sítí představuje trénovací množinu, chybovou funkci, zpětnou propagaci chyby a minimalizaci chyby pomocí gradientního sestupu. Vysvětluje také pojmy hluboké učení, batch, epocha a přeučení modelu. Závěrečný celek je věnován rekurentním sítím a Hopfieldovu modelu. Popisuje stav a aktualizaci Hopfieldovy sítě, její použití jako asociativní paměti, Hebbovo pravidlo učení, energetickou funkci, vybavování uložených vzorů a omezení kapacity sítě.

## Úprava prezentací

Při úpravě nebo tvorbě prezentací je vhodné zachovat následující strukturu:

1. Každá prezentace má vlastní adresář `ti-NN-nazev`.
2. Hlavním zdrojovým souborem je `main.tex`.
3. Obrázky specifické pro prezentaci se ukládají do jejího podadresáře `images/`.
4. Společné definice se načítají z adresáře `assets/`.
5. Titulní strana se načítá ze souboru `titlepage.tex`.
6. Soubor `pdfa.xmpi` obsahuje metadata potřebná při vytváření dokumentu ve formátu PDF/A.
7. Před dokončením změn je vhodné prezentaci zkontrolovat ve všech podporovaných poměrech stran.

Základ souboru nové prezentace může vycházet z následující struktury:

```latex
\documentclass[11pt,professionalfont,aspectratio=43]{beamer}

\input{../assets/packages.tex}
\input{../assets/theme.tex}
\input{../assets/macros.tex}
\input{../assets/listing.tex}

\def\presentationtitle{Název prezentace}

\begin{document}

    \input{../titlepage.tex}

    % Obsah prezentace

\end{document}
```

Změny v souborech `assets/theme.tex`, `assets/macros.tex`, `assets/packages.tex`, `assets/listing.tex` nebo `titlepage.tex` se mohou projevit ve všech prezentacích.

Titulní strana bere všechny údaje z příkazů `\title`, `\subtitle`, `\author`, `\email`, `\institute`, `\date` a z makra `\schoollogo`, takže ji lze beze změny použít i pro jiný předmět. Název předmětu se přepíše makrem `\subjectname` před vložením souboru `titlepage.tex`:

```latex
\def\subjectname{Matematika}
\def\presentationtitle{Derivace a~její geometrický význam}
```

Bez tohoto zápisu se použije výchozí hodnota `Teoretická informatika`.

## Autor a licence

- **Autor:** David Weber  
- **Instituce:** SPŠE Ječná
- **Kontakt:** [weber3@spsejecna.cz](mailto:weber3@spsejecna.cz)

## Použitá a doporučená literatura

1. MAREŠ, Martin a VALLA, Tomáš. *Průvodce labyrintem algoritmů.* Druhé vydání. Praha: CZ.NIC, z. s. p. o., 2022. ISBN 978-80-88168-63-8.
2. CORMEN, Thomas H.; LEISERSON, Charles Eric; RIVEST, Ronald L. a STEIN, Clifford. *Introduction to algorithms.* Fourth edition. Cambridge: The MIT Press, 2022. ISBN 978-0-262-04630-5.
3. HOPCROFT, John E.; MOTWANI, Rajeev a ULLMAN, Jeffrey D. *Introduction to automata theory, languages, and computation.* 3rd ed. Boston: Pearson/Addison Wesley, 2007.
4. MATOUŠEK, Jiří a NEŠETŘIL, Jaroslav. *Kapitoly z diskrétní matematiky.* 4., upravené a doplněné vydání. Praha: Karolinum, 2009. ISBN 978-80-246-1740-4.
5. RUSSELL, Stuart J. a NORVIG, Peter. *Artificial intelligence: A modern approach.* 3rd ed. Englewood Cliffs: Pearson, 2016. ISBN 8120323823.
6. PAPADIMITRIOU, Christos H. *Computational complexity.* Reading: Addison-Wesley, 1994. ISBN 0-201-53082-1.
7. BRYANT, Randal E. a O’HALLARON, David R. *Computer Systems: A Programmer's Perspective.* 3rd ed. Boston: Pearson, 2016. ISBN 978-0-13-409266-9.
8. ČEŠKA, Milan; HRUŠKA, Tomáš a BENEŠ, Miroslav. *Překladače.* Brno: Vysoké učení technické v Brně, Fakulta elektrotechnická, bez roku. Učební texty vysokých škol. [Dostupné online](https://www.fi.muni.cz/usr/kretinsky/prekladace_skripta_VUT.pdf). Citováno 2. 7. 2026.
9. KATZ, Jonathan a LINDELL, Yehuda. *Introduction to modern cryptography.* Boca Raton: Chapman & Hall/CRC, 2008. ISBN 978-1-58488-551-1.
10. JAMES, Gareth; WITTEN, Daniela; HASTIE, Trevor; TIBSHIRANI, Robert a TAYLOR, Jonathan E. *An introduction to statistical learning: with applications in Python.* Cham: Springer, 2023. ISBN 978-3-031-39189-7.