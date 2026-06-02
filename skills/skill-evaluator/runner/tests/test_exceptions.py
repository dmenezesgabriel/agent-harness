from runner.exceptions import ProviderAbortError


class TestProviderAbortError:
    def test_is_a_runtime_error_carrying_its_message(self) -> None:
        exc = ProviderAbortError("provider rate limit exceeded for judge call")
        assert isinstance(exc, RuntimeError)
        assert str(exc) == "provider rate limit exceeded for judge call"
