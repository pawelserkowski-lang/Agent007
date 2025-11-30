import os

print("-" * 40)
print("   RAPORT ZMIENNYCH ŚRODOWISKOWYCH")
print("-" * 40)

k1 = os.environ.get("GEMINI_KEY", "BRAK")
k2 = os.environ.get("GOOGLE_API_KEY", "BRAK")

print(f"1. GEMINI_KEY     = {k1}")
print(f"2. GOOGLE_API_KEY = {k2}")

print("-" * 40)
if "TWOJ_PRAWDZIWY" in k1 or "TWOJ_PRAWDZIWY" in k2:
    print("DIAGNOZA: W zmiennych masz WPISANY TEKST PRZYKŁADOWY zamiast klucza!")
    print("ROZWIĄZANIE: Musisz to nadpisać prawdziwym kodem od Google.")
else:
    print("Zmienne wyglądają na prawdziwe dane. Jeśli nie działa, klucz może być nieaktywny.")