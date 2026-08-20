from app.services.phone_numbers import normalize_e164, parse_phone_numbers


def test_space_separated_numbers():
    assert parse_phone_numbers("8038542105 8038540398 8038542292") == [
        "+18038542105", "+18038540398", "+18038542292"
    ]


def test_mixed_separators_and_formatting():
    assert parse_phone_numbers("(803) 854-2105, 803.854.0398; +1 803-854-2292") == [
        "+18038542105", "+18038540398", "+18038542292"
    ]


def test_duplicates_are_removed():
    assert parse_phone_numbers("8038542105\n(803) 854-2105") == ["+18038542105"]


def test_single_number_normalization():
    assert normalize_e164("803-854-2105") == "+18038542105"
