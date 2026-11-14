"""Reading text the way a person sees it (V70): one folding used by the medical gate, the question gate and the
card checks, so they all see the same string.

Three steps, in order:

1. `strip_invisible`: after NFKC, drop every format (Cf) and nonspacing mark (Mn) character, the combining grapheme
   joiner (U+034F), the Mongolian vowel separator (U+180E), the variation selectors (U+FE00 to FE0F) and the tag
   characters (U+E0000 to E007F), a few fillers that draw nothing (Hangul and Braille blanks), and every other control
   character that is not whitespace. "m<U+200E>e" is then "me".
2. `skeleton`: common Armenian, Cyrillic, Greek, Cherokee and a few other letters that look like a Latin letter are
   mapped to it (a short form of the Unicode TR39 confusables list).
3. `has_unmapped_letter`: a letter still outside ASCII after both is a letter this gate cannot read. A question that
   has one is never answered; it gets the fixed refusal (fail closed). A letter that was mapped is NOT trusted:
   `has_non_latin_letter` looks at the question before the mapping.
"""

from __future__ import annotations

import unicodedata

__all__ = ["has_non_latin_letter", "has_unmapped_letter", "is_invisible", "skeleton", "strip_invisible"]

_INVISIBLE_CODEPOINTS = frozenset(
    {0x034F, 0x180E, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x2800, 0x3164, 0xFFA0}
    | set(range(0xFE00, 0xFE10))
    | set(range(0xE0000, 0xE0080))
)


def is_invisible(ch: str) -> bool:
    """A character that draws nothing or changes how its neighbours are drawn."""
    if ord(ch) in _INVISIBLE_CODEPOINTS:
        return True
    category = unicodedata.category(ch)
    if category in {"Cf", "Mn"}:
        return True
    return category in {"Cc", "Cs", "Co", "Cn"} and not ch.isspace()


def strip_invisible(text: str) -> str:
    """NFKC, then the invisible and combining characters removed. Accents on Latin letters are folded away by the
    NFKD step in `skeleton`; here a precomposed letter ("é") stays as it is."""
    return "".join(ch for ch in unicodedata.normalize("NFKC", text) if not is_invisible(ch))


def _build_confusables() -> dict[int, str]:
    pairs: dict[str, str] = {}
    # Cyrillic (lower case; upper case is folded by `.lower()` before the lookup)
    pairs.update(
        {
            "а": "a", "в": "b", "е": "e", "к": "k", "м": "m", "н": "h", "о": "o", "р": "p", "с": "c", "т": "t", "у": "y", "х": "x",
            "і": "i", "ї": "i", "ѕ": "s", "ј": "j", "ԁ": "d", "һ": "h", "ԛ": "q", "ԝ": "w", "ӏ": "l", "ё": "e", "ѡ": "w", "ɡ": "g",
            "ґ": "r", "ғ": "f", "ү": "y", "ұ": "y", "ө": "o", "ӧ": "o", "ԍ": "g", "ᴦ": "r", "ᴨ": "n", "ɓ": "b", "ɗ": "d",
        }
    )
    # Greek
    pairs.update(
        {
            "α": "a", "β": "b", "γ": "y", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "χ": "x",
            "ϲ": "c", "ϳ": "j", "ϸ": "p", "ω": "w", "η": "n", "μ": "u", "ζ": "z", "θ": "o", "ς": "c", "ϵ": "e",
        }
    )
    # Armenian
    pairs.update(
        {
            "օ": "o", "ս": "u", "հ": "h", "ո": "n", "ց": "g", "ք": "p", "զ": "q", "լ": "l", "ա": "w", "ւ": "l", "ռ": "n", "ը": "n",
            "է": "t", "մ": "u", "ն": "u", "ժ": "d", "ձ": "d", "ե": "t",
        }
    )
    # Latin look-alikes from other blocks (IPA, small capitals, dotless letters)
    pairs.update({"ɑ": "a", "ı": "i", "ɩ": "i", "ʜ": "h", "ᴅ": "d", "ɴ": "n", "ꜱ": "s", "ᴀ": "a", "ʙ": "b", "ᴄ": "c", "ᴇ": "e", "ɢ": "g",
                  "ᴊ": "j", "ᴋ": "k", "ʟ": "l", "ᴍ": "m", "ᴏ": "o", "ᴘ": "p", "ʀ": "r", "ᴛ": "t", "ᴜ": "u", "ᴠ": "v", "ᴡ": "w", "ʏ": "y", "ᴢ": "z",
                  "ø": "o", "đ": "d", "ł": "l", "ħ": "h", "ŧ": "t"})
    table = {ord(src): dst for src, dst in pairs.items()}
    # Cherokee: the capital letters that look like a Latin letter, and their lower-case forms.
    cherokee = {"Ꭺ": "a", "Ᏼ": "b", "Ꮯ": "c", "Ꭰ": "d", "Ꭼ": "e", "Ꮐ": "g", "Ꮋ": "h", "Ꭻ": "j", "Ꮶ": "k", "Ꮮ": "l", "Ꮇ": "m", "Ꮲ": "p",
                "Ꭱ": "r", "Ꮪ": "s", "Ꭲ": "t", "Ꮩ": "v", "Ꮃ": "w", "Ꮓ": "z", "Ꭵ": "i", "Ꮖ": "i"}
    for src, dst in cherokee.items():
        table[ord(src)] = dst
        table[ord(src.lower())] = dst
    return table


_CONFUSABLES = _build_confusables()


def skeleton(text: str) -> str:
    """Lower case, invisible characters removed, accents folded and look-alike letters mapped to Latin. This is the
    view a person reads. It is used to read a question, never to decide that a question is safe: see
    `has_non_latin_letter`."""
    folded = unicodedata.normalize("NFKD", strip_invisible(text).lower())
    folded = "".join(ch for ch in folded if not is_invisible(ch))
    return folded.translate(_CONFUSABLES)


def has_non_latin_letter(text: str) -> bool:
    """True when, after the invisible characters are removed and accents are folded off Latin letters, any letter is
    outside ASCII. Hindi, Hebrew, Thai, Greek, Armenian, Cherokee, Cyrillic, Chinese, Japanese and Korean are all in
    this set, and so is a Latin look-alike from another script. A language, or a trick, the gate cannot read is never
    answered. An accent on a Latin letter ("médecin") folds away and is not foreign."""
    folded = unicodedata.normalize("NFKD", strip_invisible(text))
    folded = "".join(ch for ch in folded if not is_invisible(ch))
    return any(ch.isalpha() and ord(ch) > 127 for ch in folded)


def has_unmapped_letter(text: str) -> bool:
    """True when a letter is still outside ASCII after the skeleton: a letter with no Latin look-alike at all."""
    return any(ch.isalpha() and ord(ch) > 127 for ch in skeleton(text))
