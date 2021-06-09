entire_list = """\
account21
account22
account23
account24
account25
account26
account27
account28
account29
account30
account31
account32
account33
account34
account35
account36
account37
account38\
""".split("\n")

poll_account = "account29"

exclude_list = """\
account30
account35
account36\
""".split("\n")

final_list = [x for x in entire_list if x not in exclude_list and x != poll_account]

print(entire_list)
print(exclude_list)
print(final_list)