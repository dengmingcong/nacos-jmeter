entire_list = """\
pushUser01
pushUser02
pushUser03
pushUser04
pushUser05
pushUser06
pushUser07
pushUser08
pushUser09
pushUser10
pushUser11
pushUser12
pushUser13
pushUser14
pushUser15
pushUser16
pushUser17
pushUser18
pushUser19
pushUser20
pushUser21
pushUser22
pushUser23
pushUser24\
""".split("\n")

poll_account = "pushUser02"

exclude_list = """\
pushUser03\
""".split("\n")

final_list = [x for x in entire_list if x not in exclude_list and x != poll_account]

print(entire_list)
print(exclude_list)
print(final_list)