from pathlib import Path
for p in Path("/mnt/e/project-infi/wolf-cog-os/scripts").glob("*.sh"):
    b = p.read_bytes()
    f = b.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if f != b:
        p.write_bytes(f)
        print("fixed", p.name)
