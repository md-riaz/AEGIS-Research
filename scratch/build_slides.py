#!/usr/bin/env python3
"""Build SafeDash defense presentation from parts."""
import os

parts_dir = os.path.join(os.path.dirname(__file__), "slide_parts")
output = os.path.join(os.path.dirname(os.path.dirname(__file__)), "defense_presentation.html")

# Read all parts in order
content = ""
for i in range(1, 6):
    path = os.path.join(parts_dir, f"part{i}.txt")
    with open(path, "r", encoding="utf-8") as f:
        content += f.read()

with open(output, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Presentation written to {output}")
print(f"Size: {len(content)} bytes")
