import argparse
import contextlib
import glob
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor


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

# Překládá se i to, co se od minulého překladu nezměnilo (--force)
FORCE = False

# Adresář, kam --move přesouvá hotová PDF; nezměněné PDF se hledá i tam
MOVE_TARGET = None

# Prezentace se překládají souběžně ve více vláknech (viz compile_all). Zámek
# brání tomu, aby se řádky z různých vláken slily do jednoho, a vyrovnávací
# paměť vlákna drží pohromadě všechna hlášení o jedné variantě.
_output_lock = threading.Lock()
_thread_state = threading.local()

# Nastaví se po Ctrl+C; rozpracované překlady pak už nespouštějí další programy.
STOP = threading.Event()


def say(message=''):
    buffer = getattr(_thread_state, 'buffer', None)
    if buffer is not None:
        buffer.append(message)
        return
    with _output_lock:
        sys.stdout.write(message + '\n')
        sys.stdout.flush()


@contextlib.contextmanager
def grouped_output():
    """Vypíše hlášení vzniklá uvnitř bloku najednou, až blok skončí.

    S --verbose se nic nezdržuje: hlášení musí zůstat ve správném pořadí vůči
    syrovému výstupu programů, který jde rovnou na terminál.
    """
    if VERBOSE:
        yield
        return
    _thread_state.buffer = []
    try:
        yield
    finally:
        lines = _thread_state.buffer
        _thread_state.buffer = None
        if lines:
            with _output_lock:
                sys.stdout.write('\n'.join(lines) + '\n')
                sys.stdout.flush()


def step_started(what):
    say('%s%s Compiling %s%s' % (Style.BOLD, SYMBOLS['run'], what, Style.RESET))


def step_succeeded(what, details):
    suffix = ' %s(%s)%s' % (Style.DIM, details, Style.RESET) if details else ''
    say('%s%s Successfully compiled %s%s%s'
        % (Style.GREEN, SYMBOLS['ok'], what, Style.RESET, suffix))


def step_skipped(what):
    say('%s%s Up to date %s%s' % (Style.GREEN, SYMBOLS['ok'], what, Style.RESET))


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
    # Souběžně běžící programy se nesmějí přetahovat o vstup z terminálu.
    return subprocess.run(
        command,
        cwd=cwd or None,
        stdin=subprocess.DEVNULL,
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


# Pomocné soubory, které po sobě zanechává pdflatex a biber
AUXILIARY_SUFFIXES = (
    ".aux",
    ".out",
    ".log",
    ".synctex.gz",
    ".toc",
    ".nav",
    ".snm",
    ".vrb",
    ".bbl",
    ".bcf",
    ".blg",
    ".run.xml",
)

# Co se do pracovní kopie nepřenáší: pomocné soubory, hotová PDF a metadata
# PDF/A, která si pdfx při každém průchodu vytváří znovu.
GENERATED_SUFFIXES = AUXILIARY_SUFFIXES + (".pdf", ".xmpi")


def cleanup_files(folder):
    """Smaže z adresáře prezentace pomocné soubory, např. po překladu v editoru."""
    folder = fix_path_for_windows(folder)

    for suffix in AUXILIARY_SUFFIXES:
        for file in glob.glob(os.path.join(folder, "*" + suffix)):
            if VERBOSE:
                detail(f"Deleting {file}")
            try:
                os.remove(file)
            except OSError as e:
                note(f"could not remove {file}: {e}")


# ---------------------------------------------------------------------------
# Pracovní kopie
# ---------------------------------------------------------------------------
#
# Každá varianta se překládá ve vlastním dočasném adresáři, který zrcadlí
# kořen repozitáře. Varianty téže prezentace se díky tomu mohou překládat
# souběžně: jinak by si navzájem přepisovaly soubor pdfa.xmpi, který pdfx
# zapisuje při každém průchodu pod pevným jménem. Zdroje se nekopírují, vedou
# na ně symbolické odkazy; všechny relativní cesty ve zdrojích (../assets,
# images/..., ti-16-kryptografie/images/...) proto znějí stejně jako při
# překladu přímo v repozitáři a výsledné PDF se neliší.

def symlinks_available():
    """Zjistí, zda lze vytvářet symbolické odkazy (na Windows ne vždy)."""
    probe = tempfile.mkdtemp(prefix="compile-")
    try:
        os.symlink(probe, os.path.join(probe, "link"), target_is_directory=True)
        return True
    except (OSError, NotImplementedError, AttributeError):
        return False
    finally:
        shutil.rmtree(probe, ignore_errors=True)


SYMLINKS = symlinks_available()


def mirror_entry(source, target):
    """Zpřístupní soubor či adresář v pracovní kopii odkazem, jinak kopií."""
    if SYMLINKS:
        os.symlink(source, target, target_is_directory=os.path.isdir(source))
    elif os.path.isdir(source):
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def is_mirrored(directory, name):
    """Rozhodne, zda položka adresáře patří do pracovní kopie."""
    if name.startswith("."):
        return False
    if name.endswith(GENERATED_SUFFIXES):
        return not os.path.isfile(os.path.join(directory, name))
    return True


def create_workspace(folder):
    """
    Vytvoří pracovní kopii pro překlad prezentace v adresáři `folder` a vrátí
    dvojici (kořen kopie, jméno adresáře prezentace v ní).

    Kořen zrcadlí nadřazený adresář prezentace, tedy kořen repozitáře. Adresář
    prezentace je v kopii skutečný, protože do něj pdflatex zapisuje; odkazy
    vedou až na jeho položky.
    """
    folder = os.path.abspath(folder)
    parent = os.path.dirname(folder)
    name = os.path.basename(folder)

    # Skutečná cesta bez odkazů, aby odpovídala cestám v záznamu pdflatexu
    workspace = os.path.realpath(tempfile.mkdtemp(prefix="compile-"))
    try:
        for entry in os.listdir(parent):
            source = os.path.join(parent, entry)
            if entry == name or not is_mirrored(parent, entry):
                continue
            # Bez symbolických odkazů by se s každou variantou kopírovaly
            # i všechny ostatní prezentace; ty k překladu potřeba nejsou.
            if not SYMLINKS and os.path.isfile(os.path.join(source, "main.tex")):
                continue
            mirror_entry(source, os.path.join(workspace, entry))

        os.mkdir(os.path.join(workspace, name))
        for entry in os.listdir(folder):
            if is_mirrored(folder, entry):
                mirror_entry(os.path.join(folder, entry),
                             os.path.join(workspace, name, entry))
    except BaseException:
        shutil.rmtree(workspace, ignore_errors=True)
        raise

    return workspace, name


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

    # V pracovní kopii může být pod tímto jménem odkaz na zbytek po dřívějším
    # nedokončeném překladu; zápis skrz něj by přepsal soubor v repozitáři.
    if os.path.lexists(variant_file):
        os.remove(variant_file)

    with open(variant_file, "w", encoding="utf8") as fout:
        fout.writelines(new_lines)

    if VERBOSE:
        detail(f"Created TeX file: {variant_file}")


# ---------------------------------------------------------------------------
# Přeskakování nezměněných variant
# ---------------------------------------------------------------------------
#
# Po úspěšném překladu se k výslednému PDF uloží otisky všech souborů, které
# pdflatex a biber přečetly: zdrojů prezentace, sdílených souborů z assets/
# i balíčků a fontů z distribuce TeXu. Seznam přečtených souborů zapisuje sám
# pdflatex (přepínač -recorder, soubor .fls). Dokud se žádný z těch souborů
# nezmění a PDF je stále na místě, není co překládat a varianta se přeskočí.
# Otisky se počítají z obsahu, takže pouhá změna času souboru (např. po
# git checkout) nový překlad nevyvolá.

CACHE_DIR = ".compile-cache"

_hash_lock = threading.Lock()
_hash_cache = {}


def file_hash(path, cached=True):
    """Otisk obsahu souboru, nebo None, pokud soubor nelze přečíst."""
    if cached:
        with _hash_lock:
            if path in _hash_cache:
                return _hash_cache[path]
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as file:
            for block in iter(lambda: file.read(1 << 20), b""):
                digest.update(block)
        result = digest.hexdigest()
    except OSError:
        result = None
    if cached:
        with _hash_lock:
            _hash_cache[path] = result
    return result


# Změna skriptu může změnit způsob překladu, proto zneplatní všechny záznamy.
SCRIPT_HASH = file_hash(os.path.abspath(__file__))


def manifest_file(folder, output_name):
    """Cesta k záznamu o překladu daného PDF."""
    folder = os.path.abspath(folder)
    return os.path.join(os.path.dirname(folder), CACHE_DIR,
                        os.path.basename(folder), output_name + ".json")


def dependency_key(path, workspace):
    """
    Převede cestu přečteného souboru na klíč záznamu: soubory z repozitáře
    mají cestu relativní ke kořeni (pracovní kopie jej zrcadlí), ostatní,
    tedy soubory distribuce TeXu, cestu absolutní.
    """
    path = os.path.normpath(os.path.join(workspace, path))
    try:
        relative = os.path.relpath(path, workspace)
    except ValueError:  # jiný disk ve Windows
        return path
    if relative == os.pardir or relative.startswith(os.pardir + os.sep):
        return path
    return relative


def read_dependencies(workspace, name, stem):
    """Vrátí klíče souborů, které pdflatex a biber při překladu přečetly."""
    work_folder = os.path.join(workspace, name)
    inputs = {os.path.join(name, "main.tex")}
    outputs = set()

    with open(os.path.join(work_folder, stem + ".fls"), "r", encoding="utf-8",
              errors="surrogateescape") as fls:
        for line in fls:
            kind, _, path = line.rstrip("\r\n").partition(" ")
            if kind == "INPUT":
                inputs.add(dependency_key(path, workspace))
            elif kind == "OUTPUT":
                outputs.add(dependency_key(path, workspace))

    # Databázi zdrojů čte biber, v záznamu pdflatexu proto chybí; její cestu
    # zapisuje biblatex do souboru .bcf relativně k adresáři prezentace.
    bcf = os.path.join(work_folder, stem + ".bcf")
    if os.path.exists(bcf):
        with open(bcf, "r", encoding="utf-8", errors="replace") as file:
            for source in re.findall(
                    r"<bcf:datasource[^>]*>([^<]+)</bcf:datasource>", file.read()):
                inputs.add(dependency_key(os.path.join(name, source), workspace))

    return inputs - outputs


def save_manifest(folder, output_pdf, variant, workspace, name, stem, report,
                  started_at):
    """Uloží záznam o úspěšném překladu; při potížích se jen neuloží nic."""
    parent = os.path.dirname(os.path.abspath(folder))
    path = manifest_file(folder, os.path.basename(output_pdf))
    try:
        hashes = {}
        for key in sorted(read_dependencies(workspace, name, stem)):
            real = key if os.path.isabs(key) else os.path.join(parent, key)
            digest = file_hash(real)
            # Co v repozitáři není, vzniklo až při překladu v pracovní kopii
            # (např. main_43.tex) a závislostí není.
            if digest is None and not os.path.isabs(key):
                continue
            # Zdroj upravený během překladu: není jisté, kterou jeho podobu
            # pdflatex četl, takže se varianta příště přeloží znovu.
            if not os.path.isabs(key) and os.path.getmtime(real) >= started_at - 2:
                raise ValueError("%s changed during the build" % key)
            hashes[key] = digest
        manifest = {
            "script": SCRIPT_HASH,
            "variant": variant,
            "pdf": file_hash(output_pdf, cached=False),
            "pages": report["pages"],
            "undefined_refs": report["undefined_refs"],
            "undefined_cites": report["undefined_cites"],
            "inputs": hashes,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".tmp", "w", encoding="utf-8") as file:
            json.dump(manifest, file, ensure_ascii=False, separators=(",", ":"))
        os.replace(path + ".tmp", path)
    except (OSError, ValueError) as error:
        delete_if_exists(path)
        if VERBOSE:
            detail("Build record not saved: %s" % error)


def find_up_to_date(folder, output_pdf, variant):
    """
    Vrátí dvojici (cesta k PDF, záznam), pokud PDF z minulého překladu stále
    existuje a nic z toho, z čeho vzniklo, se nezměnilo; jinak (None, None).
    """
    parent = os.path.dirname(os.path.abspath(folder))
    try:
        with open(manifest_file(folder, os.path.basename(output_pdf)), "r",
                  encoding="utf-8") as file:
            manifest = json.load(file)
        if manifest["script"] != SCRIPT_HASH or manifest["variant"] != variant:
            return None, None

        candidates = [output_pdf]
        if MOVE_TARGET is not None:
            candidates.append(os.path.join(MOVE_TARGET, os.path.basename(output_pdf)))
        existing = [pdf for pdf in candidates
                    if file_hash(pdf, cached=False) == manifest["pdf"]]
        if not existing:
            return None, None

        for key, digest in manifest["inputs"].items():
            real = key if os.path.isabs(key) else os.path.join(parent, key)
            if digest is None or file_hash(real) != digest:
                return None, None
        return existing[0], manifest
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None, None


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


def run_pdflatex(workspace, name, stem):
    """
    Zkompiluje dokument v pořadí pdflatex, biber, pdflatex, pdflatex.
    Tři průchody pdflatexem jsou potřeba, aby se ustálily jak citace, tak
    odkazy a osnova Beameru.

    pdflatex běží v kořeni pracovní kopie `workspace` a zapisuje do adresáře
    prezentace `name`, stejně jako by běžel v kořeni repozitáře.

    Vrátí popis chyby, nebo None, pokud vše proběhlo v pořádku.
    """
    # -file-line-error nechá pdflatex hlásit chyby ve tvaru 'file.tex:12: ...',
    # takže lze místo chyby ukázat bez hádání. -recorder zapíše seznam
    # přečtených souborů (.fls), podle něhož se pozná, kdy je třeba překládat
    # znovu; na výsledné PDF vliv nemá.
    command = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-recorder",
        "-output-directory",
        name,
        "%s/%s.tex" % (name, stem),
    ]

    for i in range(3):
        if STOP.is_set():
            return INTERRUPTED
        result = run_tool(command, workspace)
        if STOP.is_set():
            return INTERRUPTED
        if result.returncode != 0:
            return ('pdflatex exited with status %d on pass %d of 3'
                    % (result.returncode, i + 1))

        if i == 0:
            reason = run_biber(os.path.join(workspace, name), stem)
            if reason is not None:
                return reason

    return None


# Důvod neúspěchu varianty, jejíž překlad přerušil uživatel klávesami Ctrl+C
INTERRUPTED = 'interrupted'

# PDF, která nebylo třeba překládat znovu (kvůli závěrečnému shrnutí)
UP_TO_DATE = []


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

    output_pdf = fix_path_for_windows(os.path.join(folder, output_name))
    variant = [aspect_suffix, bool(handout)]

    if not FORCE:
        existing, manifest = find_up_to_date(folder, output_pdf, variant)
        if existing is not None:
            with grouped_output():
                step_skipped(output_name)
                report_undefined(manifest, output_name)
            UP_TO_DATE.append(existing)
            return existing

    delete_if_exists(output_pdf)

    description_parts = []
    if aspect_suffix is not None:
        description_parts.append(f"aspect ratio {aspect_suffix}")
    description_parts.append("handout" if handout else "standard")
    description = ", ".join(description_parts)

    step_started('%s (%s)' % (title, description))
    started_at = time.time()

    # Hlášení o variantě se vypíše vcelku, i když se souběžně překládají
    # další varianty.
    with grouped_output():
        workspace, name = create_workspace(folder)
        try:
            work_folder = os.path.join(workspace, name)

            # Původní main.tex lze použít přímo pouze pro základní standardní
            # variantu; ostatní dostanou kopii s upravenými volbami třídy.
            if aspect is not None or handout:
                create_variant_tex(
                    main_file,
                    os.path.join(work_folder, source_stem + ".tex"),
                    aspect=aspect,
                    handout=handout,
                )

            reason = run_pdflatex(workspace, name, source_stem)

            if reason == INTERRUPTED:
                step_failed(output_name, reason)
                return None

            # Prázdný dokument nechá pdflatex vypsat 'No pages of output'
            # a přesto skončit s nulou, proto se ověřuje, že PDF opravdu vzniklo.
            source_pdf = os.path.join(work_folder, source_stem + ".pdf")
            if reason is None and not os.path.exists(source_pdf):
                reason = 'no PDF was produced'

            # Log posledního průchodu popisuje dokument, který byl skutečně
            # zapsán; čte se ještě před smazáním pracovní kopie.
            report = parse_log(read_log(work_folder, source_stem))

            if reason is not None:
                step_failed(output_name, reason)
                report_errors(report)
                return None

            shutil.move(source_pdf, output_pdf)
            save_manifest(folder, output_pdf, variant, workspace, name,
                          source_stem, report, started_at)

            facts = []
            if report['pages']:
                facts.append('%d pages' % report['pages'])
            facts.append(human_size(os.path.getsize(output_pdf)))
            facts.append('%.1f s' % (time.time() - started_at))
            step_succeeded(output_name, ', '.join(facts))
            report_undefined(report, output_name)
            return output_pdf
        finally:
            shutil.rmtree(workspace, ignore_errors=True)


def list_variants(handout=False, aspect_ratios=None):
    """
    Vrátí varianty jedné prezentace jako dvojice (poměr stran, handout).

    Pokud jsou zadány poměry stran, vytvoří se standardní varianta pro každý
    z nich a při --handout také odpovídající handout varianta pro každý poměr.
    Pokud poměry stran zadány nejsou, zachovává se původní chování:
    title.pdf a případně title_handout.pdf.
    """
    if aspect_ratios:
        # Odstranění duplicit při zachování pořadí.
        aspects = list(
            dict.fromkeys(normalize_aspect_ratio(aspect) for aspect in aspect_ratios)
        )
    else:
        aspects = [None]

    variants = []
    for aspect in aspects:
        variants.append((aspect, False))
        if handout:
            variants.append((aspect, True))

    return variants


def source_size(folder):
    """Celková velikost zdrojů .tex v adresáři, hrubý odhad délky překladu."""
    total = 0
    for directory, _, files in os.walk(folder):
        for name in files:
            if name.endswith('.tex'):
                total += os.path.getsize(os.path.join(directory, name))
    return total


def compile_all(presentations, jobs, handout=False, aspect_ratios=None):
    """
    Zkompiluje všechny varianty prezentací zadaných dvojicemi (adresář, název),
    nejvýše `jobs` variant najednou. Vrátí seznam výsledků v pořadí prezentací
    a jejich variant; neúspěšná varianta je v něm zastoupena hodnotou None.

    Každý pdflatex využije jediné jádro, takže souběh více překladů zkrátí
    celkovou dobu zhruba úměrně počtu jader.
    """
    variants = list_variants(handout=handout, aspect_ratios=aspect_ratios)
    tasks = [(folder, title, aspect, is_handout)
             for folder, title in presentations
             for aspect, is_handout in variants]

    def compile_task(task):
        if STOP.is_set():
            return None
        folder, title, aspect, is_handout = task
        return compile_variant(folder, title, aspect=aspect, handout=is_handout)

    try:
        if jobs <= 1 or len(tasks) <= 1:
            return [compile_task(task) for task in tasks]

        # Nejdelší překlady se zahajují první, aby na konci nečekala ostatní
        # vlákna na jeden dlouhý překlad, který se dostal na řadu pozdě.
        # Handout nemá postupné odkrývání, a tedy výrazně méně stran.
        sizes = {folder: source_size(folder) for folder, _ in presentations}
        order = sorted(
            range(len(tasks)),
            key=lambda index: sizes[tasks[index][0]] / (3 if tasks[index][3] else 1),
            reverse=True,
        )

        executor = ThreadPoolExecutor(max_workers=jobs)
        try:
            futures = {index: executor.submit(compile_task, tasks[index])
                       for index in order}
            return [futures[index].result() for index in range(len(tasks))]
        except KeyboardInterrupt:
            # Ctrl+C dostanou i běžící pdflatexy a skončí; vlákna pak už další
            # programy nespouštějí a jen po sobě uklidí.
            STOP.set()
            raise
        finally:
            executor.shutdown(wait=True, cancel_futures=True)
    finally:
        # Překlad sám v adresářích prezentací nic nezanechává; uklízí se po
        # překladech spuštěných jinak, např. z editoru.
        for folder, _ in presentations:
            cleanup_files(folder)


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
        "-j",
        "--jobs",
        type=int,
        help=(
            "How many documents to compile at the same time (default: "
            "number of CPU cores, or 1 with --verbose so that the raw output "
            "of the programs does not interleave)."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Compile everything, even documents whose sources have not "
            "changed since they were last compiled"
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

    global VERBOSE, FORCE, MOVE_TARGET
    VERBOSE = args.verbose
    FORCE = args.force
    if args.move:
        MOVE_TARGET = os.getcwd()
    setup_colors()

    if not args.all:
        if not args.folder:
            parser.error("The --folder argument is required when not using --all.")
        if not args.title:
            parser.error("The --title argument is required when not using --all.")
    elif not args.folder:
        args.folder = os.getcwd()

    if args.jobs is not None and args.jobs < 1:
        parser.error("The --jobs argument must be at least 1.")
    if args.jobs is not None:
        jobs = args.jobs
    elif VERBOSE:
        jobs = 1
    else:
        jobs = os.cpu_count() or 1

    started_at = time.time()

    if args.all:
        folders = find_presentation_folders(args.folder)
        presentations = [(folder, os.path.basename(os.path.abspath(folder)))
                         for folder in folders]
        if not folders:
            note("no %s folder with main.tex was found in %s."
                 % (PRESENTATION_DIR_PATTERN, args.folder))
    else:
        presentations = [(args.folder, args.title)]

    results = compile_all(presentations, jobs, handout=args.handout,
                          aspect_ratios=args.aspect_ratios)
    documents = len(results)
    failures = sum(1 for pdf in results if pdf is None)
    compiled_files = [pdf for pdf in results if pdf is not None]

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

    unchanged = ', %d of them up to date' % len(UP_TO_DATE) if UP_TO_DATE else ''
    say('%s%s Done: %d document(s) in %.1f s%s%s'
        % (Style.GREEN, SYMBOLS['ok'], documents, elapsed, unchanged,
           Style.RESET))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say('%s%s Interrupted%s' % (Style.RED, SYMBOLS['fail'], Style.RESET))
        raise SystemExit(130)
