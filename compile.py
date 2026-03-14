import os
import argparse
import subprocess
import glob
import platform
import re
import shutil  # Pro kopírování výsledných PDF

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
    extensions = ["*.aux", "*.out", "*.log", "*.synctex.gz", "*.toc"]
    
    print("Cleaning up auxiliary files...")
    for ext in extensions:
        for file in glob.glob(os.path.join(folder, ext)):
            print(f"Deleting {file}")
            os.remove(file)
    print("Cleanup completed.")

def add_handout_option(line):
    """
    Pokud se v řádku nachází \documentclass s obsahem "beamer",
    vloží volbu "handout" mezi volitelné parametry.
    """
    if "beamer" in line:
        pattern = r"^(?P<pre>\s*\\documentclass)(?P<opts>\s*\[[^\]]*\])?\s*(?P<brace>\{)(?P<class>[^}]+)(?P<close>\})"
        match = re.match(pattern, line)
        if match:
            pre = match.group("pre")
            opts = match.group("opts")
            brace = match.group("brace")
            class_name = match.group("class")
            close = match.group("close")
            if opts:
                opts_content = opts.strip()[1:-1].strip()
                opts_list = [opt.strip() for opt in opts_content.split(",") if opt.strip()]
                if "handout" not in opts_list:
                    opts_list.append("handout")
                new_opts = "[" + ",".join(opts_list) + "]"
            else:
                new_opts = "[handout]"
            return f"{pre}{new_opts} {brace}{class_name}{close}\n"
    return line

def create_handout_tex(main_file, handout_file):
    with open(main_file, "r", encoding="utf8") as fin:
        lines = fin.readlines()
    
    new_lines = []
    for line in lines:
        new_line = add_handout_option(line)
        new_lines.append(new_line)
    
    with open(handout_file, "w", encoding="utf8") as fout:
        fout.writelines(new_lines)
    print(f"Created handout TeX file: {handout_file}")

# --- Funkce pro úpravu poměru stran ---

def add_aspectratio_option(line, aspect):
    """
    Pokud se v řádku nachází \documentclass s obsahem "beamer",
    vloží (nebo nahradí) volbu aspectratio podle zadané hodnoty.
    Např. "16:9" se převede na "aspectratio=169".
    """
    if "beamer" in line:
        pattern = r"^(?P<pre>\s*\\documentclass)(?P<opts>\s*\[[^\]]*\])?\s*(?P<brace>\{)(?P<class>[^}]+)(?P<close>\})"
        match = re.match(pattern, line)
        if match:
            pre = match.group("pre")
            opts = match.group("opts")
            brace = match.group("brace")
            class_name = match.group("class")
            close = match.group("close")
            aspect_option = f"aspectratio={aspect.replace(':', '')}"
            if opts:
                opts_content = opts.strip()[1:-1].strip()
                opts_list = [opt.strip() for opt in opts_content.split(",") if opt.strip()]
                # Odstraníme případné již existující nastavení aspectratio
                opts_list = [opt for opt in opts_list if not opt.startswith("aspectratio=")]
                opts_list.append(aspect_option)
                new_opts = "[" + ",".join(opts_list) + "]"
            else:
                new_opts = f"[{aspect_option}]"
            return f"{pre}{new_opts} {brace}{class_name}{close}\n"
    return line

def create_aspect_tex(main_file, aspect_tex, aspect):
    with open(main_file, "r", encoding="utf8") as fin:
        lines = fin.readlines()
    
    new_lines = []
    for line in lines:
        new_line = add_aspectratio_option(line, aspect)
        new_lines.append(new_line)
    
    with open(aspect_tex, "w", encoding="utf8") as fout:
        fout.writelines(new_lines)
    print(f"Created {aspect} TeX file: {aspect_tex}")

def compile_aspect(folder, title, aspect):
    """
    Zkompiluje projekt s upraveným poměrem stran.
    Výstupní soubor bude pojmenován např. pro 16:9 jako {title}_16_9.pdf.
    """
    aspect_suffix = aspect.replace(":", "_")
    main_file = fix_path_for_windows(os.path.join(folder, "main.tex"))
    aspect_tex = fix_path_for_windows(os.path.join(folder, f"main_{aspect_suffix}.tex"))
    output_pdf_aspect = fix_path_for_windows(os.path.join(folder, f"{title}_{aspect_suffix}.pdf"))
    
    create_aspect_tex(main_file, aspect_tex, aspect)
    delete_if_exists(output_pdf_aspect)
    
    # Kompilace verze s daným poměrem stran (dvakrát)
    for i in range(2):
        print(f"Compiling {aspect_tex} for {aspect} version... (Run {i+1})")
        subprocess.run(["pdflatex", "-output-directory", folder, aspect_tex])
    
    source_pdf = fix_path_for_windows(os.path.join(folder, f"main_{aspect_suffix}.pdf"))
    os.rename(source_pdf, output_pdf_aspect)
    print(f"{aspect} compilation completed. Output file: {output_pdf_aspect}")
    
    delete_if_exists(aspect_tex)
    cleanup_files(folder)

# --- Ostatní funkce ---

def compile_handout(folder, title):
    main_file = fix_path_for_windows(os.path.join(folder, "main.tex"))
    handout_tex = fix_path_for_windows(os.path.join(folder, "main_handout.tex"))
    output_pdf_handout = fix_path_for_windows(os.path.join(folder, f"{title}_handout.pdf"))

    create_handout_tex(main_file, handout_tex)
    delete_if_exists(output_pdf_handout)

    # Kompilace handout verze (dvakrát)
    for i in range(2):
        print(f"Compiling {handout_tex} for handout... (Run {i+1})")
        subprocess.run(["pdflatex", "-output-directory", folder, handout_tex])
    
    source_pdf = fix_path_for_windows(os.path.join(folder, "main_handout.pdf"))
    os.rename(source_pdf, output_pdf_handout)
    print(f"Handout compilation completed. Output file: {output_pdf_handout}")

    delete_if_exists(handout_tex)
    cleanup_files(folder)

def compile_latex(folder, title, handout=False, aspect_ratios=None):
    folder = fix_path_for_windows(folder)

    # Kompilace standardní verze, která se považuje za 4:3
    main_file = fix_path_for_windows(os.path.join(folder, "main.tex"))
    output_pdf = fix_path_for_windows(os.path.join(folder, f"{title}.pdf"))

    delete_if_exists(output_pdf)

    # Kompilace standardní verze (dvakrát)
    for i in range(2):
        print(f"Compiling {main_file}... (Run {i+1})")
        subprocess.run(["pdflatex", "-output-directory", folder, main_file])

    source_pdf = fix_path_for_windows(os.path.join(folder, "main.pdf"))
    os.rename(source_pdf, output_pdf)
    print(f"Compilation completed. Output file: {output_pdf}")
    
    cleanup_files(folder)

    # Pokud byly zadány dodatečné poměry stran, vytvoříme pro každý z nich dodatečnou verzi
    if aspect_ratios:
        for aspect in aspect_ratios:
            compile_aspect(folder, title, aspect)
    
    if handout:
        compile_handout(folder, title)

def main():
    parser = argparse.ArgumentParser(
        description="LaTeX Document Compiler. Compiles a LaTeX file twice and renames the output PDF. "
                    "For beamer documents, the optional --handout flag creates an additional handout version. "
                    "With -ars (--aspect-ratios) you can specify one or more additional aspect ratios (e.g. 16:9 16:10). "
                    "If --all is specified, all subdirectories containing main.tex are processed; the output PDF "
                    "is named after the folder name. Option --move moves all resulting PDFs to the current directory."
    )
    parser.add_argument("-f", "--folder",
                        help="Path to the folder containing the LaTeX projects (or a single project). "
                             "Not required if --all is specified (default: current directory).")
    parser.add_argument("-t", "--title",
                        help="Title for the output PDF file (without .pdf). Not needed if --all is specified.")
    parser.add_argument("--all", action="store_true",
                        help="Compile main.tex in all subdirectories (each output PDF is named after its folder)")
    parser.add_argument("--handout", action="store_true",
                        help="Generate handout version for beamer presentations")
    parser.add_argument("--move", action="store_true",
                        help="Move all resulting PDFs to the current (root) directory")
    parser.add_argument("-ars", "--aspect-ratios", nargs="+", default=[],
                        help="List of aspect ratios to compile additional versions (e.g. 16:9 16:10). "
                             "If omitted, only the 4:3 variant is generated.")

    args = parser.parse_args()

    if not args.all:
        if not args.folder:
            parser.error("The --folder argument is required when not using --all.")
        if not args.title:
            parser.error("The --title argument is required when not using --all.")
    else:
        if not args.folder:
            args.folder = os.getcwd()

    compiled_files = []

    if args.all:
        for root, dirs, files in os.walk(args.folder):
            if "main.tex" in files:
                title = os.path.basename(os.path.abspath(root))
                print(f"Found main.tex in {root}, compiling as '{title}.pdf'")
                compile_latex(root, title, handout=args.handout, aspect_ratios=args.aspect_ratios)
                compiled_pdf = fix_path_for_windows(os.path.join(root, f"{title}.pdf"))
                compiled_files.append(compiled_pdf)
                if args.aspect_ratios:
                    for aspect in args.aspect_ratios:
                        aspect_suffix = aspect.replace(":", "_")
                        compiled_pdf_aspect = fix_path_for_windows(os.path.join(root, f"{title}_{aspect_suffix}.pdf"))
                        compiled_files.append(compiled_pdf_aspect)
                if args.handout:
                    handout_pdf = fix_path_for_windows(os.path.join(root, f"{title}_handout.pdf"))
                    compiled_files.append(handout_pdf)
        if not compiled_files:
            print("No main.tex files were found in any subdirectories.")
    else:
        compile_latex(args.folder, args.title, handout=args.handout, aspect_ratios=args.aspect_ratios)
        compiled_pdf = fix_path_for_windows(os.path.join(args.folder, f"{args.title}.pdf"))
        compiled_files.append(compiled_pdf)
        if args.aspect_ratios:
            for aspect in args.aspect_ratios:
                aspect_suffix = aspect.replace(":", "_")
                compiled_pdf_aspect = fix_path_for_windows(os.path.join(args.folder, f"{args.title}_{aspect_suffix}.pdf"))
                compiled_files.append(compiled_pdf_aspect)
        if args.handout:
            handout_pdf = fix_path_for_windows(os.path.join(args.folder, f"{args.title}_handout.pdf"))
            compiled_files.append(handout_pdf)

    if args.move:
        dest = os.getcwd()
        print(f"Copying compiled PDFs to {dest}")
        for pdf in compiled_files:
            if os.path.exists(pdf):
                dest_file = os.path.join(dest, os.path.basename(pdf))
                print(f"Moving {pdf} to {dest_file}")
                shutil.move(pdf, dest_file)
            else:
                print(f"File {pdf} does not exist and cannot be moved.")

if __name__ == "__main__":
    main()
