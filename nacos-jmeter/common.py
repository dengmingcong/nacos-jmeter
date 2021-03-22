from loguru import logger
import os
import platform
import subprocess
import textwrap


def concatenate_files(files: list, out: str, to_stdout=False):
    """
    Combine content of several files, and save it to another file.
    :param files: list of files to be concatenated
    :param out: file to save concatenated text
    :param to_stdout: print to stdout if set True
    """
    with open(out, "w", encoding="utf-8") as out_file:
        # print("# all properties collected", file=out_file)
        out_file.write("# all properties collected from Nacos snapshot")
        for file in files:
            # out_file.write(f"# file: {file}\n")
            header = textwrap.dedent(f"""\n
            #=============== properties collected from ===============
            # {file}
            #=========================================================
            """)
            print(header, file=out_file)
            with open(file, 'r', encoding="utf-8") as in_file:
                # shutil.copyfileobj(in_file, out_file)
                out_file.write(in_file.read())
    logger.debug(f"File generated: {out}")

    if to_stdout:
        with open(out, 'r', encoding="utf-8") as out_file:
            print(out_file.read())


def convert_property_file(property_file, out):
    """call native2ascii to convert property file to fit ISO 8859-1."""
    sys_os = platform.system()
    if sys_os == "Windows":
        raise ValueError("\nCalling on Windows platform is not supported yet, run command below in cmd instead.\n"
                         r"\path\to\jdk\bin\native2ascii.exe -encoding UTF-8 src.properties dst.properties")
    else:
        native2ascii_basename = "native2ascii"
    # first, get JAVA_HOME from env
    java_home = os.getenv('JAVA_HOME')
    # if JAVA_HOME not set, get from javac command
    if not java_home:
        logger.debug("env JAVA_HOME not set, read link of javac")
        java_home = subprocess.check_output(
            'dirname $(dirname $(readlink -f $(which javac)))', shell=True, universal_newlines=True
        ).split('\n')[0]
    logger.debug(f"JAVA_HOME: {java_home}")
    native2ascii_full_path = os.path.join(java_home, 'bin', native2ascii_basename)
    logger.debug(f"native2ascii: {native2ascii_full_path}")
    result = subprocess.run([native2ascii_full_path, '-encoding', 'UTF-8', property_file, out])
    logger.debug(f"Arguments: {result.args}")
