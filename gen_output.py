#!/usr/bin/env python3
"""Generate the actual Python source text for fa, ps, fr sections."""
import json
import ast
import sys

# We need to read the en section structure from the actual file to match comment groupings
# But since we just need the dict entries, let's format them properly.

with open('C:/github/Telegram-shop-Physical/en_keys.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

# Read the actual file to get the en section with comments
with open('C:/github/Telegram-shop-Physical/bot/i18n/strings.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find en section start/end line numbers
lines = content.split('\n')
en_start_line = None
for i, line in enumerate(lines):
    if '"en": {' in line:
        en_start_line = i
        break

# Extract comment structure from en section
en_section_lines = []
depth = 0
started = False
for i in range(en_start_line, len(lines)):
    line = lines[i]
    if '"en": {' in line:
        depth = 1
        started = True
        continue
    if started:
        for ch in line:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
        if depth <= 0:
            break
        en_section_lines.append(line)

# Extract comments and their positions relative to keys
comments = []
for line in en_section_lines:
    stripped = line.strip()
    if stripped.startswith('#'):
        comments.append(('comment', stripped))
    elif stripped.startswith('"'):
        # Extract key
        key = stripped.split('"')[1]
        comments.append(('key', key))
    elif stripped == '':
        comments.append(('blank', ''))

# Now load the translation dicts
# We'll exec the gen scripts
sys.path.insert(0, 'C:/github/Telegram-shop-Physical')

# Load fa from gen_translations.py
fa_ns = {}
exec(open('C:/github/Telegram-shop-Physical/gen_translations.py', encoding='utf-8').read(), fa_ns)
fa = fa_ns['fa']

ps_ns = {}
exec(open('C:/github/Telegram-shop-Physical/gen_all_translations.py', encoding='utf-8').read(), ps_ns)
ps = ps_ns['ps']
fr = ps_ns['fr']

def format_value(v):
    """Format a string value for Python source, using double quotes."""
    # We need to properly escape the value
    # Use repr but switch to double quotes
    r = repr(v)
    if r.startswith("'"):
        # Convert single-quoted repr to double-quoted
        inner = r[1:-1]
        # Unescape single quotes, escape double quotes
        inner = inner.replace("\\'", "'")
        inner = inner.replace('"', '\\"')
        return '"' + inner + '"'
    return r

def generate_section(lang_code, translations, comment_structure):
    """Generate a Python source section for a language."""
    lines = []
    lines.append(f'    "{lang_code}": {{')

    for item_type, item_value in comment_structure:
        if item_type == 'comment':
            lines.append(f'        {item_value}')
        elif item_type == 'blank':
            lines.append('')
        elif item_type == 'key':
            key = item_value
            if key in translations:
                val = format_value(translations[key])
                lines.append(f'        "{key}": {val},')

    lines.append('    },')
    return '\n'.join(lines)

# Generate all three sections
fa_section = generate_section('fa', fa, comments)
ps_section = generate_section('ps', ps, comments)
fr_section = generate_section('fr', fr, comments)

# Write to output file
with open('C:/github/Telegram-shop-Physical/translation_sections.txt', 'w', encoding='utf-8') as f:
    f.write(fa_section)
    f.write('\n')
    f.write(ps_section)
    f.write('\n')
    f.write(fr_section)
    f.write('\n')

print(f"FA section: {fa_section.count(chr(10))+1} lines")
print(f"PS section: {ps_section.count(chr(10))+1} lines")
print(f"FR section: {fr_section.count(chr(10))+1} lines")

# Count keys per section
for name, section in [("fa", fa_section), ("ps", ps_section), ("fr", fr_section)]:
    count = section.count('": "')
    # also count '": \'' patterns
    count2 = section.count("\": '")
    print(f"  {name} key entries: {count + count2}")
