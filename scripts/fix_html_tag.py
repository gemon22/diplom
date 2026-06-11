p = r"d:\Diplom\tour-generator-module\frontend\index.html"
text = open(p, encoding="utf-8").read()
text = text.replace("</motion>", "</div>")
open(p, "w", encoding="utf-8").write(text)
print("fixed")
