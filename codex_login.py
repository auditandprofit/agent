import requests
from bs4 import BeautifulSoup

LOGIN_URL = "https://chatgpt.com/auth/login"


def parse_login_page(session: requests.Session) -> dict:
    """Retrieve the login page and return dict of form inputs."""
    resp = session.get(LOGIN_URL)
    if resp.status_code != 200:
        return {}
    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form")
    payload = {}
    if form:
        for inp in form.find_all("input"):
            name = inp.get("name")
            if not name:
                continue
            payload[name] = inp.get("value", "")
    return payload


def attempt_login(email: str, password: str) -> requests.Response:
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    })
    payload = parse_login_page(session)
    payload.update({"email": email, "password": password})
    resp = session.post(LOGIN_URL, data=payload)
    return resp


if __name__ == "__main__":
    response = attempt_login("user@example.com", "incorrect_password")
    print("Status:", response.status_code)
    print("Body snippet:", response.text[:200])
