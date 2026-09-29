from importlib.metadata import version

import diagram_generator


def test_editable_install() -> None:
    assert version("requirement-to-diagram") == "0.1.0"
    assert diagram_generator.__file__ is not None
