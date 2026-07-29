import nltk
from nltk.corpus import stopwords
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
import yake
from deep_translator import GoogleTranslator
from django.utils.html import strip_tags

# --- Загрузка стоп-слов NLTK ---
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

# Базовые стоп-слова + научные служебные слова
RU_STOPWORDS = set(stopwords.words('russian'))
EXTRA_STOPWORDS = {
    'статье', 'статья', 'рассматривается', 'рассмотрен', 'анализируется', 'анализ',
    'описывается', 'показано', 'установлено', 'обосновано', 'предложено', 'разработано',
    'является', 'представляет', 'выступает', 'рассмотрены', 'приведены', 'используется',
    'позволяет', 'обеспечивает', 'связан', 'основан', 'направлен', 'целью', 'задачей',
    'роль', 'обеспечении', 'деятельности', 'примере', 'основе', 'результате', 'ходе',
    'рамках', 'целях', 'отношении', 'случае', 'виде', 'плане', 'мере', 'силе',
    'данных', 'данный', 'данная', 'данное', 'данные', 'также', 'кроме', 'того',
    'благодаря', 'вследствие', 'посредством', 'путем', 'счет', 'числе', 'частности'
}
ALL_STOPWORDS = RU_STOPWORDS | EXTRA_STOPWORDS

# --- Singleton ---
_yake_extractor = None


def _get_yake():
    global _yake_extractor
    if _yake_extractor is None:
        _yake_extractor = yake.KeywordExtractor(
            lan="ru",
            n=2,
            dedupLim=0.7,
            top=20,
            stopwords=list(ALL_STOPWORDS)
        )
    return _yake_extractor


def generate_annotation(text: str, sentences_count: int = 3) -> str:
    """Экстрактивная суммаризация текста статьи на русском (Sumy LSA)."""
    clean = strip_tags(text) if text else ""
    clean = clean.strip()
    if len(clean) < 100:
        return ""

    try:
        parser = PlaintextParser.from_string(clean, Tokenizer("russian"))
        summarizer = LsaSummarizer(Stemmer("russian"))
        summarizer.stop_words = frozenset(ALL_STOPWORDS)
        sentences = summarizer(parser.document, sentences_count)
        return " ".join(str(s) for s in sentences) if sentences else ""
    except Exception as e:
        print(f"[Sumy error] {e}")
        return ""


def extract_keywords(text: str, max_keywords: int = 10) -> str:
    """Извлечение ключевых слов через YAKE. Возвращает строку через запятую."""
    clean = strip_tags(text) if text else ""
    clean = clean.strip()
    if len(clean) < 30:
        return ""

    try:
        extractor = _get_yake()
        keywords = extractor.extract_keywords(clean)
        filtered = []
        for kw, score in keywords:
            words = kw.lower().split()
            # Убираем фразы, где все слова — стоп-слова или короткие
            if any(w not in ALL_STOPWORDS and len(w) > 2 for w in words):
                # Убираем фразы, начинающиеся/заканчивающиеся на предлог/местоимение
                if words[0] not in RU_STOPWORDS and words[-1] not in RU_STOPWORDS:
                    filtered.append(kw)
            if len(filtered) >= max_keywords:
                break
        return ", ".join(filtered)
    except Exception as e:
        print(f"[YAKE error] {e}")
        return ""


def translate_text(text: str, source_lang: str = "ru", target_lang: str = "en") -> str:
    """Перевод через deep-translator (GoogleTranslator)."""
    if not text or not text.strip():
        return ""
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return translator.translate(text)
    except Exception as e:
        print(f"[Translate error] {e}")
        return ""