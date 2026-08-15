import argparse
import glob
import os
import platform
import re
import shutil
import subprocess


# Prezentace jsou pouze v adresářích ti-* přímo v kořeni repozitáře. Rekurzivní
# průchod by zabral i pomocné adresáře (např. .claude/worktrees) s vlastním main.tex.
PRESENTATION_DIR_PATTERN = "ti-*"


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
        print(f"File {file_path} exists, deleting it...")
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
    ]

    print("Cleaning up auxiliary files...")
    for ext in extensions:
        for file in glob.glob(os.path.join(folder, ext)):
            print(f"Deleting {file}")
            os.remove(file)
    print("Cleanup completed.")


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

    variant_description = []
    if aspect is not None:
        variant_description.append(f"aspect ratio {normalize_aspect_ratio(aspect)}")
    if handout:
        variant_description.append("handout")

    description = ", ".join(variant_description) or "standard"
    print(f"Created TeX file for {description}: {variant_file}")


def run_pdflatex(folder, tex_file, description):
    for i in range(2):
        print(f"Compiling {tex_file} ({description})... (Run {i + 1})")
        result = subprocess.run(
            ["pdflatex", "-output-directory", folder, tex_file],
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"pdflatex failed while compiling {tex_file} "
                f"(run {i + 1}, exit code {result.returncode})."
            )


def compile_variant(folder, title, aspect=None, handout=False):
    """
    Zkompiluje jednu variantu prezentace.

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

    # Původní main.tex lze použít přímo pouze pro základní standardní variantu.
    is_original_main = aspect is None and not handout
    if is_original_main:
        tex_file = main_file
    else:
        tex_file = fix_path_for_windows(os.path.join(folder, f"{source_stem}.tex"))
        create_variant_tex(main_file, tex_file, aspect=aspect, handout=handout)

    output_pdf = fix_path_for_windows(os.path.join(folder, f"{output_stem}.pdf"))
    source_pdf = fix_path_for_windows(os.path.join(folder, f"{source_stem}.pdf"))

    delete_if_exists(output_pdf)

    description_parts = []
    if aspect_suffix is not None:
        description_parts.append(f"aspect ratio {aspect_suffix}")
    description_parts.append("handout" if handout else "standard")
    description = ", ".join(description_parts)

    try:
        run_pdflatex(folder, tex_file, description)

        if not os.path.exists(source_pdf):
            raise FileNotFoundError(
                f"Expected output file {source_pdf} was not created."
            )

        os.replace(source_pdf, output_pdf)
        print(f"Compilation completed. Output file: {output_pdf}")
    finally:
        if not is_original_main:
            delete_if_exists(tex_file)
        cleanup_files(folder)

    return output_pdf


def compile_latex(folder, title, handout=False, aspect_ratios=None):
    """
    Zkompiluje požadované varianty a vrátí seznam vytvořených PDF.

    Pokud jsou zadány poměry stran, vytvoří se standardní varianta pro každý
    z nich a při --handout také odpovídající handout varianta pro každý poměr.
    Pokud poměry stran zadány nejsou, zachovává se původní chování:
    title.pdf a případně title_handout.pdf.
    """
    compiled_files = []
    aspect_ratios = aspect_ratios or []

    if aspect_ratios:
        # Odstranění duplicit při zachování pořadí.
        normalized_aspects = list(
            dict.fromkeys(normalize_aspect_ratio(aspect) for aspect in aspect_ratios)
        )

        for aspect in normalized_aspects:
            compiled_files.append(
                compile_variant(folder, title, aspect=aspect, handout=False)
            )
            if handout:
                compiled_files.append(
                    compile_variant(folder, title, aspect=aspect, handout=True)
                )
    else:
        compiled_files.append(
            compile_variant(folder, title, aspect=None, handout=False)
        )
        if handout:
            compiled_files.append(
                compile_variant(folder, title, aspect=None, handout=True)
            )

    return compiled_files


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

    args = parser.parse_args()

    if not args.all:
        if not args.folder:
            parser.error("The --folder argument is required when not using --all.")
        if not args.title:
            parser.error("The --title argument is required when not using --all.")
    elif not args.folder:
        args.folder = os.getcwd()

    compiled_files = []

    if args.all:
        found_any = False

        for folder in find_presentation_folders(args.folder):
            found_any = True
            title = os.path.basename(os.path.abspath(folder))
            print(f"Found main.tex in {folder}, compiling as '{title}'")
            compiled_files.extend(
                compile_latex(
                    folder,
                    title,
                    handout=args.handout,
                    aspect_ratios=args.aspect_ratios,
                )
            )

        if not found_any:
            print(
                f"No {PRESENTATION_DIR_PATTERN} folder with main.tex was found "
                f"in {args.folder}."
            )
    else:
        compiled_files.extend(
            compile_latex(
                args.folder,
                args.title,
                handout=args.handout,
                aspect_ratios=args.aspect_ratios,
            )
        )

    if args.move:
        dest = os.getcwd()
        print(f"Moving compiled PDFs to {dest}")

        for pdf in compiled_files:
            if not os.path.exists(pdf):
                print(f"File {pdf} does not exist and cannot be moved.")
                continue

            dest_file = os.path.join(dest, os.path.basename(pdf))
            if os.path.abspath(pdf) == os.path.abspath(dest_file):
                print(f"File {pdf} is already in the destination directory.")
                continue

            print(f"Moving {pdf} to {dest_file}")
            shutil.move(pdf, dest_file)


if __name__ == "__main__":
    main()
