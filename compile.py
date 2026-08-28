import argparse
import glob
import os
import platform
import re
import shutil
import subprocess
import sys
import time


# Prezentace jsou pouze v adresářích ti-* přímo v kořeni repozitáře. Rekurzivní
# průchod by zabral i pomocné adresáře (např. .claude/worktrees) s vlastním main.tex.
PRESENTATION_DIR_PATTERN = "ti-*"


# ---------------------------------------------------------------------------
# Výpis do terminálu
# ---------------------------------------------------------------------------
#
# Nástroje LaTeXu jsou nesmírně upovídané: jediný průchod vypíše několik set
# řádků se seznamem všech načtených balíčků a fontů, mezi nimiž zanikne ten
# jeden řádek, na kterém záleží. Celý výstup se proto zachytí a vypíše se jen
# krátké shrnutí; zachycený log se rozebere a ukáže podrobně teprve tehdy,
# když se něco pokazí. Přepínač --verbose vrátí syrový výstup.

class Style:
    """ANSI sekvence, vypnuté tam, kde je terminál neumí zobrazit."""

    ENABLED = False

    RESET = ''
    BOLD = ''
    DIM = ''
    RED = ''
    GREEN = ''
    YELLOW = ''
    CYAN = ''

    @classmethod
    def enable(cls):
        cls.ENABLED = True
        cls.RESET = '\033[0m'
        cls.BOLD = '\033[1m'
        cls.DIM = '\033[2m'
        cls.RED = '\033[31m'
        cls.GREEN = '\033[32m'
        cls.YELLOW = '\033[33m'
        cls.CYAN = '\033[36m'


def setup_colors():
    # https://no-color.org/ -- výslovné odhlášení, které respektuje řada nástrojů
    if os.environ.get('NO_COLOR') is not None:
        return
    if not sys.stdout.isatty():
        return
    if os.name == 'nt':
        # Konzole Windows rozumí ANSI sekvencím teprve tehdy, když se pro
        # výstupní handle zapne zpracování virtuálního terminálu.
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                return
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            if not kernel32.SetConsoleMode(handle, mode.value | 0x0004):
                return
        except Exception:
            return
    Style.enable()


# Značky výsledku jednotlivých kroků; konzole starších Windows je nemusí umět
# zakódovat, proto prostá náhrada.
def pick_symbols():
    marks = {'ok': '✔', 'fail': '✘', 'warn': '⚠', 'run': '▶'}
    try:
        for mark in marks.values():
            mark.encode(sys.stdout.encoding or 'ascii')
    except (UnicodeEncodeError, LookupError):
        marks = {'ok': '+', 'fail': 'x', 'warn': '!', 'run': '>'}
    return marks


SYMBOLS = pick_symbols()

# Syrový výstup spouštěných programů se vypisuje místo krátkého shrnutí
VERBOSE = False


def say(message=''):
    print(message, flush=True)


def step_started(what):
    say('%s%s Compiling %s%s' % (Style.BOLD, SYMBOLS['run'], what, Style.RESET))


def step_succeeded(what, details):
    suffix = ' %s(%s)%s' % (Style.DIM, details, Style.RESET) if details else ''
    say('%s%s Successfully compiled %s%s%s'
        % (Style.GREEN, SYMBOLS['ok'], what, Style.RESET, suffix))


def step_failed(what, reason):
    say('%s%s Failed to compile %s: %s%s'
        % (Style.RED, SYMBOLS['fail'], what, reason, Style.RESET))


def note(message):
    say('  %s%s %s%s' % (Style.YELLOW, SYMBOLS['warn'], message, Style.RESET))


def detail(message):
    say('  %s%s%s' % (Style.DIM, message, Style.RESET))


def human_size(byte_count):
    for unit in ('B', 'kB', 'MB', 'GB'):
        if byte_count < 1024 or unit == 'GB':
            if unit == 'B':
                return '%d %s' % (byte_count, unit)
            return '%.1f %s' % (byte_count, unit)
        byte_count /= 1024.0


# ---------------------------------------------------------------------------
# Čtení logu pdflatexu
# ---------------------------------------------------------------------------

# pdflatex láme log na 79 znacích, každý vzor níže se proto musí vejít na
# začátek řádku. To všechny splňují: každá zde uvedená hláška začíná v nultém
# sloupci a na další řádek se může přelít jen její konec.
LOG_LINE_LIMIT = 120

# S přepínačem -file-line-error hlásí pdflatex chyby ve tvaru 'file.tex:12: ...',
# takže je místo chyby známé bez sledování zanoření vkládaných souborů v logu.
FILE_LINE_ERROR = re.compile(r'^(?:\./)?([^:()\s]\S*\.\w+):(\d+): (.*)$')

# Chyby bez udané pozice, např. 'Emergency stop' nebo chybějící balíček
BARE_ERROR = re.compile(r'^! (.*)$')

# "LaTeX Warning: Reference `foo' on page 12 undefined on input line 34."
UNDEFINED_REFERENCE = re.compile(r"^LaTeX Warning: Reference [`']([^']+)'")

# Neznámý klíč citace hlásí biblatex jménem LaTeXu i vlastním jménem, a to
# v jednoduchých uvozovkách, kdežto samotný LaTeX otevírá obrácenou čárkou.
UNDEFINED_CITATION = re.compile(
    r"^(?:LaTeX|Package biblatex) Warning: Citation [`']([^']+)'")

# 'Output written on main_43.pdf (32 pages, 1204830 bytes).'
OUTPUT_WRITTEN = re.compile(r'Output written on \S+ \((\d+) pages?, (\d+) bytes\)')


def read_log(folder, stem):
    log_path = os.path.join(folder, stem + '.log')
    if not os.path.exists(log_path):
        return None
    with open(log_path, 'r', encoding='utf-8', errors='replace') as log_file:
        return log_file.read()


def parse_log(text):
    """Vybere z logu pdflatexu to podstatné."""
    report = {
        'errors': [],            # (pozice, hláška, okolní řádky)
        'fatal': [],             # chyby, které pdflatex hlásí bez pozice
        'undefined_refs': [],    # návěští
        'undefined_cites': [],   # klíče citací
        'pages': None,
        'bytes': None,
    }
    if not text:
        return report

    lines = text.split('\n')
    for index, line in enumerate(lines):
        match = FILE_LINE_ERROR.match(line)
        if match:
            message = match.group(3).strip()
            # '==> Fatal error occurred' jen zopakuje, že byl překlad vzdán;
            # skutečná příčina už je zaznamenaná výše.
            if message.startswith('==>'):
                report['fatal'].append((None, shorten(message), []))
                continue
            location = '%s:%s' % (match.group(1), match.group(2))
            report['errors'].append((location, shorten(message),
                                     error_context(lines, index)))
            continue

        match = BARE_ERROR.match(line)
        if match:
            # Díky -file-line-error se chyba se známou pozicí hlásí výše ve
            # tvaru 'file:line:', takže co stále začíná '!', je buď závěrečné
            # shrnutí 'Fatal error', nebo problém, na který nelze ukázat,
            # např. chybějící balíček.
            report['fatal'].append((None, shorten(match.group(1).strip()),
                                    error_context(lines, index)))
            continue

        match = UNDEFINED_REFERENCE.match(line)
        if match:
            report['undefined_refs'].append(match.group(1))
            continue

        match = UNDEFINED_CITATION.match(line)
        if match:
            report['undefined_cites'].append(match.group(1))
            continue

        match = OUTPUT_WRITTEN.search(line)
        if match:
            report['pages'] = int(match.group(1))
            report['bytes'] = int(match.group(2))

    return report


def shorten(message):
    message = message.rstrip()
    if len(message) > LOG_LINE_LIMIT:
        return message[:LOG_LINE_LIMIT - 3] + '...'
    return message


# Řádky, které ukončují citovaný vstup a zahajují závěrečné hlášení pdflatexu
CONTEXT_END = re.compile(r'^(Here is how much|No pages of output|Output written|'
                         r'Transcript written|\s*\d+ strings out of)')


def error_context(lines, index, limit=4):
    """Pár řádků za chybou, které obvykle citují vadný vstup."""
    context = []
    for line in lines[index + 1:index + 1 + limit]:
        stripped = line.rstrip()
        if not stripped:
            break
        if stripped.startswith('!') or FILE_LINE_ERROR.match(stripped):
            break
        if CONTEXT_END.match(stripped):
            break
        context.append(shorten(stripped))
    return context


def report_errors(report):
    # Užitečné jsou chyby s pozicí; holé shrnutí 'Fatal error occurred' se
    # vypíše, jen když pdflatex nic lepšího neposkytl.
    errors = report['errors'] or report['fatal']
    for location, message, context in errors[:5]:
        if location:
            say('    %s%s%s: %s%s%s'
                % (Style.CYAN, location, Style.RESET,
                   Style.RED, message, Style.RESET))
        else:
            say('    %s%s%s' % (Style.RED, message, Style.RESET))
        for line in context:
            detail('  ' + line)
    remaining = len(errors) - 5
    if remaining > 0:
        detail('  ... and %d further error(s), see the .log file' % remaining)
    if not errors:
        detail('  pdflatex reported no error in the .log file')


def report_undefined(report, name):
    """Upozorní na odkazy a citace, které se nepodařilo rozřešit.

    Nerozřešený odkaz vysází LaTeX jako '??', chybějící citaci jako '[?]';
    klíč citace musí být v assets/literatura.bib.
    """
    if report['undefined_refs']:
        labels = sorted(set(report['undefined_refs']))
        note('%d undefined reference(s) in %s, %d distinct label(s):'
             % (len(report['undefined_refs']), name, len(labels)))
        for label in labels[:10]:
            detail('  %s' % label)
        if len(labels) > 10:
            detail('  ... and %d more' % (len(labels) - 10))
    if report['undefined_cites']:
        labels = sorted(set(report['undefined_cites']))
        note('%d undefined citation(s): %s' % (len(report['undefined_cites']),
                                               ', '.join(labels[:10])))


# ---------------------------------------------------------------------------
# Spouštění jednotlivých programů
# ---------------------------------------------------------------------------

def run_tool(command, cwd=None):
    """Spustí jeden program řetězce a zachytí jeho výstup, není-li --verbose."""
    if VERBOSE:
        return subprocess.run(command, cwd=cwd or None)
    return subprocess.run(
        command,
        cwd=cwd or None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def show_captured_output(result):
    """Vypíše zachycený výstup programu, který selhal."""
    if VERBOSE or not getattr(result, 'stdout', None):
        return
    for line in result.stdout.decode('utf-8', 'replace').splitlines():
        if line.strip():
            detail('  ' + line.rstrip())


def find_presentation_folders(root):
    """
    Vrátí seřazený seznam adresářů ti-* ležících přímo v `root`, které obsahují
    main.tex. Do hlubších úrovní se nesestupuje.
    """
    folders = []

    for path in sorted(glob.glob(os.path.join(root, PRESENTATION_DIR_PATTERN))):
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "main.tex")):
            folders.append(path)

    return folders


def fix_path_for_windows(path):
    if platform.system() == "Windows":
        return path.replace("\\", "/")
    return path


def delete_if_exists(file_path):
    if os.path.exists(file_path):
        if VERBOSE:
            detail(f"Deleting {file_path}")
        os.remove(file_path)


def cleanup_files(folder):
    folder = fix_path_for_windows(folder)
    extensions = [
        "*.aux",
        "*.out",
        "*.log",
        "*.synctex.gz",
        "*.toc",
        "*.nav",
        "*.snm",
        "*.vrb",
        "*.bbl",
        "*.bcf",
        "*.blg",
        "*.run.xml",
    ]

    for ext in extensions:
        for file in glob.glob(os.path.join(folder, ext)):
            if VERBOSE:
                detail(f"Deleting {file}")
            try:
                os.remove(file)
            except OSError as e:
                note(f"could not remove {file}: {e}")


def normalize_aspect_ratio(aspect):
    """
    Převede zápisy jako 16:10, 16_10 nebo 1610 na hodnotu 1610,
    kterou používá volba Beameru aspectratio i název výsledného souboru.
    """
    normalized = re.sub(r"\D", "", aspect)
    if not normalized:
        raise ValueError(f"Invalid aspect ratio: {aspect!r}")
    return normalized


def update_documentclass_options(line, aspect=None, handout=False):
    r"""
    Upraví volby třídy beamer v řádku \\documentclass:
      - nastaví zadaný poměr stran,
      - přidá nebo odebere volbu handout.

    Ostatní volby i případný text za příkazem \documentclass zůstanou zachovány.
    """
    pattern = (
        r"^(?P<pre>\s*\\documentclass)"
        r"(?P<opts>\s*\[[^\]]*\])?"
        r"\s*(?P<brace>\{)"
        r"(?P<class>[^}]+)"
        r"(?P<close>\})"
        r"(?P<post>.*)$"
    )

    newline = "\n" if line.endswith("\n") else ""
    line_without_newline = line.rstrip("\r\n")
    match = re.match(pattern, line_without_newline)

    if not match or match.group("class").strip() != "beamer":
        return line

    opts = match.group("opts")
    if opts:
        opts_content = opts.strip()[1:-1].strip()
        opts_list = [opt.strip() for opt in opts_content.split(",") if opt.strip()]
    else:
        opts_list = []

    # Poměr stran nahrazujeme pouze tehdy, pokud byl pro danou variantu zadán.
    if aspect is not None:
        normalized_aspect = normalize_aspect_ratio(aspect)
        opts_list = [opt for opt in opts_list if not opt.startswith("aspectratio=")]
        opts_list.append(f"aspectratio={normalized_aspect}")

    # U generovaných variant nastavujeme handout explicitně, aby se nepřenášel
    # omylem z původního souboru do standardní verze.
    opts_list = [opt for opt in opts_list if opt != "handout"]
    if handout:
        opts_list.append("handout")

    new_opts = f"[{','.join(opts_list)}]" if opts_list else ""

    return (
        f"{match.group('pre')}{new_opts} "
        f"{match.group('brace')}{match.group('class')}{match.group('close')}"
        f"{match.group('post')}{newline}"
    )


def create_variant_tex(main_file, variant_file, aspect=None, handout=False):
    with open(main_file, "r", encoding="utf8") as fin:
        lines = fin.readlines()

    new_lines = [
        update_documentclass_options(line, aspect=aspect, handout=handout)
        for line in lines
    ]

    with open(variant_file, "w", encoding="utf8") as fout:
        fout.writelines(new_lines)

    if VERBOSE:
        detail(f"Created TeX file: {variant_file}")


def run_biber(folder, stem):
    """
    Sestaví bibliografii pro daný dokument. Biber se spouští s pracovním
    adresářem prezentace, aby se relativní cesta k ../assets/literatura.bib
    v \\addbibresource rozřešila stejně jako při běhu pdflatexu.

    Vrátí popis chyby, nebo None, pokud vše proběhlo v pořádku.
    """
    result = run_tool(["biber", stem], folder)
    if result.returncode != 0:
        show_captured_output(result)
        return 'biber exited with status %d' % result.returncode
    return None


def run_pdflatex(folder, tex_file, stem):
    """
    Zkompiluje dokument v pořadí pdflatex, biber, pdflatex, pdflatex.
    Tři průchody pdflatexem jsou potřeba, aby se ustálily jak citace, tak
    odkazy a osnova Beameru.

    Vrátí popis chyby, nebo None, pokud vše proběhlo v pořádku.
    """
    # -file-line-error nechá pdflatex hlásit chyby ve tvaru 'file.tex:12: ...',
    # takže lze místo chyby ukázat bez hádání.
    command = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-output-directory",
        folder,
        tex_file,
    ]

    for i in range(3):
        result = run_tool(command)
        if result.returncode != 0:
            return ('pdflatex exited with status %d on pass %d of 3'
                    % (result.returncode, i + 1))

        if i == 0:
            reason = run_biber(folder, stem)
            if reason is not None:
                return reason

    return None


def compile_variant(folder, title, aspect=None, handout=False):
    """
    Zkompiluje jednu variantu prezentace a vrátí cestu k výslednému PDF,
    nebo None, pokud se překlad nezdařil.

    Příklady výstupů:
      - bez poměru stran: prezentace.pdf
      - bez poměru stran, handout: prezentace_handout.pdf
      - poměr 43: prezentace_43.pdf
      - poměr 43, handout: prezentace_43_handout.pdf
    """
    folder = fix_path_for_windows(folder)
    main_file = fix_path_for_windows(os.path.join(folder, "main.tex"))

    aspect_suffix = normalize_aspect_ratio(aspect) if aspect is not None else None

    stem_parts = ["main"]
    output_parts = [title]

    if aspect_suffix is not None:
        stem_parts.append(aspect_suffix)
        output_parts.append(aspect_suffix)

    if handout:
        stem_parts.append("handout")
        output_parts.append("handout")

    source_stem = "_".join(stem_parts)
    output_stem = "_".join(output_parts)
    output_name = output_stem + ".pdf"

    # Původní main.tex lze použít přímo pouze pro základní standardní variantu.
    is_original_main = aspect is None and not handout
    if is_original_main:
        tex_file = main_file
    else:
        tex_file = fix_path_for_windows(os.path.join(folder, f"{source_stem}.tex"))
        create_variant_tex(main_file, tex_file, aspect=aspect, handout=handout)

    output_pdf = fix_path_for_windows(os.path.join(folder, output_name))
    source_pdf = fix_path_for_windows(os.path.join(folder, f"{source_stem}.pdf"))

    delete_if_exists(output_pdf)

    description_parts = []
    if aspect_suffix is not None:
        description_parts.append(f"aspect ratio {aspect_suffix}")
    description_parts.append("handout" if handout else "standard")
    description = ", ".join(description_parts)

    step_started('%s (%s)' % (title, description))
    started_at = time.time()

    try:
        reason = run_pdflatex(folder, tex_file, source_stem)

        # Prázdný dokument nechá pdflatex vypsat 'No pages of output' a přesto
        # skončit s nulou, proto se ověřuje, že PDF opravdu vzniklo.
        if reason is None and not os.path.exists(source_pdf):
            reason = 'no PDF was produced'

        # Log posledního průchodu popisuje dokument, který byl skutečně zapsán;
        # čte se ještě před úklidem pomocných souborů.
        report = parse_log(read_log(folder, source_stem))

        if reason is not None:
            step_failed(output_name, reason)
            report_errors(report)
            return None

        os.replace(source_pdf, output_pdf)

        facts = []
        if report['pages']:
            facts.append('%d pages' % report['pages'])
        facts.append(human_size(os.path.getsize(output_pdf)))
        facts.append('%.1f s' % (time.time() - started_at))
        step_succeeded(output_name, ', '.join(facts))
        report_undefined(report, output_name)
        return output_pdf
    finally:
        if not is_original_main:
            delete_if_exists(tex_file)
        cleanup_files(folder)


def compile_latex(folder, title, handout=False, aspect_ratios=None):
    """
    Zkompiluje požadované varianty a vrátí seznam výsledků; neúspěšná varianta
    je v něm zastoupena hodnotou None.

    Pokud jsou zadány poměry stran, vytvoří se standardní varianta pro každý
    z nich a při --handout také odpovídající handout varianta pro každý poměr.
    Pokud poměry stran zadány nejsou, zachovává se původní chování:
    title.pdf a případně title_handout.pdf.
    """
    results = []
    aspect_ratios = aspect_ratios or []

    if aspect_ratios:
        # Odstranění duplicit při zachování pořadí.
        normalized_aspects = list(
            dict.fromkeys(normalize_aspect_ratio(aspect) for aspect in aspect_ratios)
        )

        for aspect in normalized_aspects:
            results.append(compile_variant(folder, title, aspect=aspect, handout=False))
            if handout:
                results.append(
                    compile_variant(folder, title, aspect=aspect, handout=True)
                )
    else:
        results.append(compile_variant(folder, title, aspect=None, handout=False))
        if handout:
            results.append(compile_variant(folder, title, aspect=None, handout=True))

    return results


def main():
    parser = argparse.ArgumentParser(
        description=(
            "LaTeX Document Compiler. Compiles a LaTeX file twice and renames "
            "the output PDF. For beamer documents, --handout creates a handout "
            "version for every requested aspect ratio. With -ar "
            "(--aspect-ratios) you can specify one or more aspect ratios, for "
            "example 43 1610 or 4:3 16:10. If --all is specified, every ti-* "
            "folder directly inside the target directory that contains "
            "main.tex is processed; the output PDF is named after the folder "
            "name. Option --move moves all resulting PDFs to the current "
            "directory."
        )
    )
    parser.add_argument(
        "-f",
        "--folder",
        help=(
            "Path to the folder containing the LaTeX projects (or a single "
            "project). Not required if --all is specified (default: current "
            "directory)."
        ),
    )
    parser.add_argument(
        "-t",
        "--title",
        help="Title for the output PDF file (without .pdf). Not needed if --all is specified.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Compile main.tex in every ti-* folder directly inside the target "
            "directory (each output PDF is named after its folder)"
        ),
    )
    parser.add_argument(
        "--handout",
        action="store_true",
        help="Generate a handout version for every compiled aspect ratio",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move all resulting PDFs to the current (root) directory",
    )
    parser.add_argument(
        "-ar",
        "-ars",
        "--aspect-ratios",
        nargs="+",
        default=[],
        help=(
            "List of aspect ratios to compile, e.g. 43 1610 or 4:3 16:10. "
            "When supplied, output filenames contain the normalized ratio."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help=(
            "Show the raw output of pdflatex and of the other programs instead "
            "of the short summary"
        ),
    )

    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose
    setup_colors()

    if not args.all:
        if not args.folder:
            parser.error("The --folder argument is required when not using --all.")
        if not args.title:
            parser.error("The --title argument is required when not using --all.")
    elif not args.folder:
        args.folder = os.getcwd()

    compiled_files = []
    documents = 0
    failures = 0
    started_at = time.time()

    def record(results):
        nonlocal documents, failures
        documents += len(results)
        failures += sum(1 for pdf in results if pdf is None)
        compiled_files.extend(pdf for pdf in results if pdf is not None)

    if args.all:
        folders = find_presentation_folders(args.folder)

        for folder in folders:
            title = os.path.basename(os.path.abspath(folder))
            record(
                compile_latex(
                    folder,
                    title,
                    handout=args.handout,
                    aspect_ratios=args.aspect_ratios,
                )
            )

        if not folders:
            note("no %s folder with main.tex was found in %s."
                 % (PRESENTATION_DIR_PATTERN, args.folder))
    else:
        record(
            compile_latex(
                args.folder,
                args.title,
                handout=args.handout,
                aspect_ratios=args.aspect_ratios,
            )
        )

    if args.move and compiled_files:
        dest = os.getcwd()
        moved = 0

        for pdf in compiled_files:
            if not os.path.exists(pdf):
                note('%s does not exist and cannot be moved.' % pdf)
                continue

            dest_file = os.path.join(dest, os.path.basename(pdf))
            if os.path.abspath(pdf) == os.path.abspath(dest_file):
                continue

            shutil.move(pdf, dest_file)
            moved += 1

        detail('Moved %d PDF file(s) to %s' % (moved, dest))

    elapsed = time.time() - started_at
    if failures:
        say('%s%s Finished with errors after %.1f s: %d of %d document(s) failed%s'
            % (Style.RED, SYMBOLS['fail'], elapsed, failures, documents,
               Style.RESET))
        raise SystemExit(1)

    say('%s%s Done: %d document(s) in %.1f s%s'
        % (Style.GREEN, SYMBOLS['ok'], documents, elapsed, Style.RESET))


if __name__ == "__main__":
    main()
