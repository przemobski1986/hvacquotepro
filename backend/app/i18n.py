from fastapi import Request

MESSAGES = {
    "en": {
        "auth.invalid_credentials": "Invalid email or password.",
        "auth.inactive_user": "User is inactive.",
        "auth.unauthorized": "Not authenticated.",
        "auth.forbidden": "You don't have permission to perform this action.",
        "common.not_found": "Resource not found.",
        "common.validation_failed": "Validation failed.",
        "quote.margin_below_min": "Margin is below tenant minimum.",
        "quote.sell_below_cost": "Sell price is below cost.",
    },
    "pl": {
        "auth.invalid_credentials": "Nieprawidłowy e-mail lub hasło.",
        "auth.inactive_user": "Użytkownik jest nieaktywny.",
        "auth.unauthorized": "Brak uwierzytelnienia.",
        "auth.forbidden": "Brak uprawnień do wykonania tej operacji.",
        "common.not_found": "Nie znaleziono zasobu.",
        "common.validation_failed": "Walidacja nie powiodła się.",
        "quote.margin_below_min": "Marża jest poniżej minimum ustawionego dla firmy.",
        "quote.sell_below_cost": "Cena sprzedaży jest niższa niż koszt.",
    },
}

def get_lang(request: Request) -> str:
    # Very simple Accept-Language parsing
    al = (request.headers.get("accept-language") or "").lower()
    if al.startswith("pl"):
        return "pl"
    return "en"

def t(request: Request, key: str) -> str:
    lang = get_lang(request)
    return MESSAGES.get(lang, MESSAGES["en"]).get(key, key)
