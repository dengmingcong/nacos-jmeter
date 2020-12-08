import textwrap


def combine_files(files: list, out: str):
    """
    Combine content of several files, and save it to another file.

    :param files: a list of files
    :param out: file to save concatenated text
    """
    with open(out, "w") as out_file:
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
            with open(file, 'r') as in_file:
                # shutil.copyfileobj(in_file, out_file)
                out_file.write(in_file.read())
