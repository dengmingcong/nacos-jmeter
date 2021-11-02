entire_list = """\
bannerUser01
bannerUser02
bannerUser03
bannerUser04
bannerUser05
bannerUser06
bannerUser07
bannerUser08
bannerUser09
bannerUser10
bannerUser11
bannerUser12
bannerUser13
bannerUser14
bannerUser15
bannerUser16
bannerUser17
bannerUser18
bannerUser19
bannerUser20
bannerUser21
bannerUser22
bannerUser23
bannerUser24
bannerUser25
bannerUser26
bannerUser27
bannerUser28
bannerUser29
bannerUser30
bannerUser31
bannerUser32
bannerUser33
bannerUser34
bannerUser35
bannerUser36\
""".split("\n")

poll_account = "bannerUser16"

exclude_list = """\
bannerUser18\
""".split("\n")

final_list = [x for x in entire_list if x not in exclude_list and x != poll_account]

print(entire_list)
print(exclude_list)
print(final_list)