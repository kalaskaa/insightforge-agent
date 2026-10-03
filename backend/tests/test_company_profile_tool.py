from backend.app.tools.company_profile import get_company_profile


def test_tesla_has_a_company_profile() -> None:
    profile = get_company_profile.invoke({"company": "Tesla"})

    assert profile
    assert "Tesla" in profile


def test_byd_has_a_company_profile() -> None:
    profile = get_company_profile.invoke({"company": "BYD"})

    assert profile
    assert "BYD" in profile


def test_unsupported_company_has_no_profile() -> None:
    profile = get_company_profile.invoke({"company": "Rivian"})

    assert profile == "No profile is available for Rivian."