from app.domain.normalization import (
    normalize_category_display_name,
    normalize_category_name,
    normalize_email,
    normalize_product_code,
)


def test_normalize_email():
    assert (
        normalize_email(
            "  ADMIN@LOOPANDLOVE.COM  "
        )
        == "admin@loopandlove.com"
    )


def test_normalize_product_code():
    assert (
        normalize_product_code(
            "  oso-001  "
        )
        == "OSO-001"
    )


def test_normalize_category_display_name():
    assert (
        normalize_category_display_name(
            "  Amigurumis   Crochet  "
        )
        == "Amigurumis Crochet"
    )


def test_normalize_category_name():
    assert (
        normalize_category_name(
            "  AmIgUrUmIs   CrOcHeT  "
        )
        == "amigurumis crochet"
    )


def test_category_name_normalization_is_case_insensitive():
    assert (
        normalize_category_name(
            "Decoración"
        )
        == normalize_category_name(
            "DECORACIÓN"
        )
    )