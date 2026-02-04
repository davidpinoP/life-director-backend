from app.core.authority import AuthorityFilter

test_phrases = [
    "Intenta usar el móvil menos de 30 minutos",
    "Trata de ver la tele solo 1 hora",
    "No uses redes sociales más de 15 minutos",
    "Podrías limitar el teléfono a 2 horas"
]

for phrase in test_phrases:
    filtered = AuthorityFilter.filter_text(phrase)
    print(f"Original: {phrase}")
    print(f"Filtered: {filtered}")
    print("-" * 20)
