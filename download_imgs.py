import re

with open("facebook_imgs.txt", "r", encoding="utf-8") as f:
    all_lines = ""
    for line in f.readlines():
        all_lines += line.strip()
    img_lines = re.findall("<img [^>]+>", all_lines)
    img_srcs = []
    for img in img_lines:
        img_srcs.append(re.findall("src=\"[^\"]+\"", img))
    print((img_srcs))