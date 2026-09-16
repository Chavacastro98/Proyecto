import os

dir_telemetria2 = r"c:\Proyecto\Proyecto\telemetria2"

for root, dirs, files in os.walk(dir_telemetria2):
    for f in files:
        if f.endswith(".py"):
            p = os.path.join(root, f)
            with open(p, "r", encoding="utf-8") as fp:
                c = fp.read()
            c_new = c.replace("from telemetria.", "from telemetria2.")
            c_new = c_new.replace("import telemetria.", "import telemetria2.")
            c_new = c_new.replace("package 'telemetria'", "package 'telemetria2'")
            c_new = c_new.replace("python -m telemetria", "python -m telemetria2")
            if c_new != c:
                with open(p, "w", encoding="utf-8") as fp:
                    fp.write(c_new)
                print(f"Updated imports in: {f}")

print("Done updating imports in telemetria2.")
