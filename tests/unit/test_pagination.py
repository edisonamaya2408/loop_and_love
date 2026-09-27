import pytest

from app.application.dto.pagination import (
    PaginationParams,
)


def test_pagination_defaults():
    pagination = PaginationParams.from_values()

    assert pagination.page == 1
    assert pagination.per_page == 12
    assert pagination.offset == 0


def test_pagination_calculates_offset():
    pagination = PaginationParams.from_values(
        page=3,
        per_page=12,
    )

    assert pagination.offset == 24


def test_pagination_accepts_string_values():
    pagination = PaginationParams.from_values(
        page="2",
        per_page="20",
    )

    assert pagination.page == 2
    assert pagination.per_page == 20
    assert pagination.offset == 20


def test_pagination_rejects_invalid_page():
    with pytest.raises(
        ValueError,
        match="page debe ser un número entero",
    ):
        PaginationParams.from_values(
            page="abc"
        )


def test_pagination_rejects_page_zero():
    with pytest.raises(
        ValueError,
        match="page debe ser mayor que cero",
    ):
        PaginationParams.from_values(
            page=0
        )


def test_pagination_rejects_negative_page():
    with pytest.raises(
        ValueError,
        match="page debe ser mayor que cero",
    ):
        PaginationParams.from_values(
            page=-1
        )


def test_pagination_rejects_invalid_per_page():
    with pytest.raises(
        ValueError,
        match="per_page debe ser un número entero",
    ):
        PaginationParams.from_values(
            per_page="abc"
        )


def test_pagination_rejects_per_page_zero():
    with pytest.raises(
        ValueError,
        match="per_page debe ser mayor que cero",
    ):
        PaginationParams.from_values(
            per_page=0
        )


def test_pagination_rejects_per_page_above_maximum():
    with pytest.raises(
        ValueError,
        match="per_page no puede ser mayor que 50",
    ):
        PaginationParams.from_values(
            per_page=51
        )

def test_pagination_rejects_page_above_maximum():
    with pytest.raises(
        ValueError,
        match="page no puede ser mayor que 10000",
    ):
        PaginationParams.from_values(
            page=10001
        )


def test_pagination_accepts_maximum_page():
    pagination = (
        PaginationParams.from_values(
            page=10000,
            per_page=50,
        )
    )

    assert pagination.page == 10000
    assert pagination.per_page == 50
    assert pagination.offset == 499950