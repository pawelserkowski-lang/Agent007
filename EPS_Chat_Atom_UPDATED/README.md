
# EPS 7.0 – Core Model Manager

To jest backendowy moduł EPS 7.0 odpowiedzialny za:
- automatyczne pobieranie list modeli od dostawców, którzy udostępniają endpoint list-models,
- cache lokalny,
- grupowanie modeli po providerach i możliwościach (capabilities),
- prosty CLI do podglądu.

## Obsługiwani dostawcy (wszyscy mają endpoint list-models):

- OpenAI
- Google Gemini
- Anthropic (Claude)
- Mistral AI
- Cohere
- xAI (Grok)
- Groq
- Together AI
- DeepSeek
- Amazon Bedrock (opcjonalnie, multi-provider)

## Jak uruchomić demo

1. Ustaw zmienne środowiskowe z kluczami API, np.:

   - `OPENAI_API_KEY`
   - `GEMINI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `MISTRAL_API_KEY`
   - `COHERE_API_KEY`
   - `XAI_API_KEY`
   - `GROQ_API_KEY`
   - `TOGETHER_API_KEY`
   - `DEEPSEEK_API_KEY`
   - (opcjonalnie) `BEDROCK_API_KEY`

2. Zainstaluj zależności:

   ```bash
   pip install requests
   ```

3. Uruchom:

   ```bash
   python -m eps7.app
   ```

Zobaczysz listę modeli pogrupowaną po providerach.
