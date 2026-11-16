"""Funcții comune testelor de API."""


def register(client, email="ana@exemplu.ro", password="parola-secreta", display_name="Ana"):
    response = client.post("/auth/register", json={"email": email, "password": password, "display_name": display_name})
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_headers(client, email="ana@exemplu.ro") -> dict[str, str]:
    return auth_header(register(client, email=email)["access_token"])
