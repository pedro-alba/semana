import os

import pytest


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    # ponytail: SEMANA_CHROMIUM points to an installed Chromium; without it, Playwright's own is used
    path = os.environ.get("SEMANA_CHROMIUM")
    return {**browser_type_launch_args, **({"executable_path": path} if path else {})}
