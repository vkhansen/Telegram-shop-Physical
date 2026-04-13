"""One-shot script: insert btn.ai_assistant after btn.my_tickets in strings.py"""
import pathlib

path = pathlib.Path("bot/i18n/strings.py")
content = path.read_text(encoding="utf-8")

# Russian feature-section entry (unique Cyrillic value)
russian_old = '        "btn.my_tickets": "🎫 Поддержка",'
russian_new = russian_old + '\n        "btn.ai_assistant": "🤖 ИИ-помощник",'

# English-value entries (all other 8 occurrences)
english_old = '        "btn.my_tickets": "🎫 Support",'
english_new = english_old + '\n        "btn.ai_assistant": "🤖 AI Assistant",'

print("Russian occurrences:", content.count(russian_old))
print("English occurrences:", content.count(english_old))

content = content.replace(russian_old, russian_new)
content = content.replace(english_old, english_new)

print("Russian remaining:", content.count(russian_old))
print("English remaining:", content.count(english_old))
print("Russian ai_assistant lines:", content.count('"btn.ai_assistant": "🤖 ИИ-помощник"'))
print("English ai_assistant lines:", content.count('"btn.ai_assistant": "🤖 AI Assistant"'))

path.write_text(content, encoding="utf-8")
print("Done.")
