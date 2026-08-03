from pathlib import Path
import re

pattern = re.compile(r'(<form[^>]*id="formEditar"[^>]*)(>)')
updated = 0

for path in Path('.').rglob('*.html'):
    text = path.read_text(encoding='utf-8')

    def repl(m):
        tag = m.group(1)
        if 'data-confirm=' in tag:
            return m.group(0)
        return tag + ' data-confirm="¿Guardar cambios?"' + m.group(2)

    new_text = pattern.sub(repl, text)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
        print(path)
        updated += 1

print(f'Updated {updated} files')
