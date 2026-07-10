from platform_forge.utils.strings import split_csv


def test_split_csv_ignores_empty_items() -> None:
    assert split_csv("pricing, inventory,, fulfillment ") == [
        "pricing",
        "inventory",
        "fulfillment",
    ]
