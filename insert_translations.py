#!/usr/bin/env python3
"""Insert the three translation sections into strings.py."""

# Read the current file
with open('C:/github/Telegram-shop-Physical/bot/i18n/strings.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Read the translation sections
with open('C:/github/Telegram-shop-Physical/translation_sections.txt', 'r', encoding='utf-8') as f:
    new_sections = f.read()

# The file ends with:
#     },
# }
# We need to insert before the final }
# Find the last occurrence of "\n}" which is the closing of TRANSLATIONS dict
# The ar section ends with "    }," and then the file has "}"

# Find the insertion point: right before the final "}\n" at end of file
# The file should end with "    },\n}\n"
rindex = content.rstrip().rfind('}')
# This should be the final } of TRANSLATIONS
# The one before it should be the closing }, of ar section

# Let's be more precise: find "    },\n}" at the end
insert_marker = "    },\n}"
pos = content.rfind(insert_marker)
if pos == -1:
    print("ERROR: Could not find insertion point")
    exit(1)

# Insert after "    }," (the ar closing) and before "\n}"
insert_pos = pos + len("    },")

new_content = content[:insert_pos] + "\n" + new_sections + content[insert_pos:]

# Write the modified file
with open('C:/github/Telegram-shop-Physical/bot/i18n/strings.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Insertion complete!")
print(f"Original size: {len(content)} chars")
print(f"New size: {len(new_content)} chars")
print(f"Added: {len(new_content) - len(content)} chars")
