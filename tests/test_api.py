def make_note(client, category_id, title="Standup", content="Discuss sprint"):
    return client.post(
        "/notes", json={"title": title, "content": content, "category_id": category_id}
    )


def test_create_and_list_categories(client):
    resp = client.post("/categories", json={"name": "personal"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "personal"

    assert [c["name"] for c in client.get("/categories").json()] == ["personal"]


def test_duplicate_category_returns_409(client, category):
    resp = client.post("/categories", json={"name": "work"})
    assert resp.status_code == 409


def test_create_and_get_note(client, category):
    resp = make_note(client, category["id"])
    assert resp.status_code == 201
    note = resp.json()
    assert note["id"] and note["created_at"]

    assert client.get(f"/notes/{note['id']}").json() == note


def test_create_note_with_missing_category_returns_422(client):
    resp = make_note(client, category_id=999)
    assert resp.status_code == 422
    assert client.get("/notes").json() == []


def test_search_filters_by_title(client, category):
    make_note(client, category["id"], title="Standup notes")
    make_note(client, category["id"], title="Grocery list")

    titles = [n["title"] for n in client.get("/notes", params={"search": "Standup"}).json()]
    assert titles == ["Standup notes"]


def test_patch_only_changes_sent_fields(client, category):
    note = make_note(client, category["id"]).json()

    resp = client.patch(f"/notes/{note['id']}", json={"title": "Retro"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Retro"
    assert resp.json()["content"] == note["content"]


def test_patch_to_missing_category_returns_422(client, category):
    note = make_note(client, category["id"]).json()

    resp = client.patch(f"/notes/{note['id']}", json={"category_id": 999})
    assert resp.status_code == 422
    assert client.get(f"/notes/{note['id']}").json()["category_id"] == category["id"]


def test_missing_note_returns_404(client):
    assert client.get("/notes/999").status_code == 404
    assert client.patch("/notes/999", json={"title": "x"}).status_code == 404
    assert client.delete("/notes/999").status_code == 404


def test_delete_note(client, category):
    note = make_note(client, category["id"]).json()

    assert client.delete(f"/notes/{note['id']}").status_code == 200
    assert client.get(f"/notes/{note['id']}").status_code == 404


def test_delete_category_with_notes_returns_409(client, category):
    note = make_note(client, category["id"]).json()

    assert client.delete(f"/categories/{category['id']}").status_code == 409

    client.delete(f"/notes/{note['id']}")
    assert client.delete(f"/categories/{category['id']}").status_code == 200
