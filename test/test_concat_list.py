entire_list = """\
account01
account02
account03
account04
account05
account06\
""".split("\n")

exclude_list = """\
account01
account04\
""".split("\n")

final_list = [x for x in entire_list if x not in exclude_list]

print(entire_list)
print(exclude_list)
print(final_list)