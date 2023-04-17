import pytest
from flask_login import logout_user
import logging


def test_login_required(client):
    client.post()
    response = client.get("/logout")
    response = client.get("/overview")

    assert response == True
    # assert response.request.path 

    # session is saved now

    # assert response.json["username"] == "flask"