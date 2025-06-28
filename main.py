
import re

def extract_named_links(text):
    pattern = re.compile(r"(.*?)\n\s*\[([^\]]+)\]\((https?://[^)]+)\)", re.DOTALL)
    matches = pattern.findall(text)
    return [(match[1], match[2]) for match in matches]

# Пример
description = """
h2. Продукт: Glory
Гео: PK
Ставка: 9
Валюта: $
Капа: 500 fd daily
Сорс: FB
Баер: @dzho666

h2. ПП:glory

Пакистан линки (домен под вас):

Reg.Form
[Reg.Form](https://click.example.com/?landing=2943&sub_id1={subid}&sub_id2=JOO)

Wheel Girls
[Wheel Girls](https://click.example.com/?landing=2944&sub_id1={subid}&sub_id2=JOO)
"""

print(extract_named_links(description))
