from elmybots.config import DefaultConfig


def test_start():
    config = DefaultConfig()

    assert type(config.PORT) == int
