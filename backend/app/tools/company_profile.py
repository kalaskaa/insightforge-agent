from langchain_core.tools import tool


COMPANY_PROFILES = {
    "Tesla": "Tesla is a US-based electric vehicle and clean energy company.",
    "BYD": "BYD is a China-based manufacturer of electric vehicles and batteries.",
    "Tata Motors": "Tata Motors is an India-based automobile manufacturer.",
    "Mahindra": "Mahindra is an India-based company with automotive and mobility businesses.",
}


@tool
def get_company_profile(company: str) -> str:
    """Return a short neutral profile for Tesla, BYD, Tata Motors, or Mahindra."""
    profile = COMPANY_PROFILES.get(company)
    if profile is None:
        return f"No profile is available for {company}."

    return profile