from dataclasses import dataclass


@dataclass(frozen=True)
class AIProvider:
    slug: str
    name: str
    key_prefix: str
    console_url: str
    description: str


PROVIDERS: dict[str, AIProvider] = {
    "gemini": AIProvider(
        slug="gemini",
        name="Google Gemini",
        key_prefix="",
        console_url="https://aistudio.google.com/app/apikey",
        description="Gemini models from Google AI Studio.",
    ),
}


def get_provider(slug: str) -> AIProvider | None:
    return PROVIDERS.get(slug)


def mask_key(value: str) -> str:
    """Return a short, non-reversible hint such as sk-...9f2a."""
    cleaned = value.strip()
    if len(cleaned) <= 8:
        return "*" * len(cleaned)
    return f"{cleaned[:3]}...{cleaned[-4:]}"
