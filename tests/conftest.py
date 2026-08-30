import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests against a running Docker Compose stack.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-e2e"):
        return

    skip_e2e = pytest.mark.skip(
        reason="E2E tests require a running Docker Compose stack; use --run-e2e."
    )
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)
