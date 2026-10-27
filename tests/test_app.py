import pytest

from app import create_app, validate_student


@pytest.fixture()
def app(tmp_path):
    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DATABASE": str(tmp_path / "test_students.db"),
    })
    yield test_app


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username="admin", password="admin123"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def add_sample_student(client, prn="PRN12345"):
    return client.post(
        "/students/add",
        data={
            "name": "Arya Student",
            "prn": prn,
            "department": "Computer Engineering",
        },
        follow_redirects=True,
    )


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Staff Login" in response.data


def test_valid_admin_login(client):
    response = login(client)
    assert response.status_code == 200
    assert b"Student Records" in response.data


def test_invalid_login_is_rejected(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=True,
    )
    assert b"Invalid username or password." in response.data


def test_students_page_requires_login(client):
    response = client.get("/students")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_add_student(client):
    login(client)
    response = add_sample_student(client)
    assert b"Student added successfully." in response.data
    assert b"Arya Student" in response.data


def test_edit_student(client):
    login(client)
    add_sample_student(client)
    response = client.post(
        "/students/1/edit",
        data={
            "name": "Updated Student",
            "prn": "PRN54321",
            "department": "Information Technology",
        },
        follow_redirects=True,
    )
    assert b"Student updated successfully." in response.data
    assert b"Updated Student" in response.data


def test_delete_student(client):
    login(client)
    add_sample_student(client)
    response = client.post("/students/1/delete", follow_redirects=True)
    assert b"Student deleted successfully." in response.data
    assert b"Arya Student" not in response.data


def test_duplicate_prn_is_rejected(client):
    login(client)
    add_sample_student(client)
    response = add_sample_student(client)
    assert b"A student with that PRN already exists." in response.data


def test_required_fields_are_validated(client):
    login(client)
    response = client.post(
        "/students/add",
        data={"name": "", "prn": "", "department": ""},
        follow_redirects=True,
    )
    assert b"Student name, PRN, and department are required." in response.data


def test_staff_can_login(client):
    response = login(client, "staff", "staff123")
    assert response.status_code == 200
    assert b"Student Records" in response.data


def test_logout(client):
    login(client)
    response = client.get("/logout", follow_redirects=True)
    assert b"Staff Login" in response.data
    assert b"You have been logged out." in response.data


def test_validate_student_accepts_valid_details():
    error = validate_student(
        "Arya Student",
        "PRN12345",
        "Computer Engineering",
    )
    assert error is None


@pytest.mark.parametrize(
    ("name", "prn", "department", "expected_error"),
    [
        (
            "",
            "PRN12345",
            "Computer Engineering",
            "Student name, PRN, and department are required.",
        ),
        (
            "A" * 101,
            "PRN12345",
            "Computer Engineering",
            "Student name must be 100 characters or fewer.",
        ),
        (
            "12345",
            "PRN12345",
            "Computer Engineering",
            "Student name must contain at least one letter.",
        ),
        (
            "Arya Student",
            "A" * 41,
            "Computer Engineering",
            "PRN must be 40 characters or fewer.",
        ),
        (
            "Arya Student",
            "PRN@123",
            "Computer Engineering",
            "PRN can contain only letters, numbers, and internal hyphens.",
        ),
        (
            "Arya Student",
            "PRN12345",
            "D" * 101,
            "Department must be 100 characters or fewer.",
        ),
        (
            "Arya Student",
            "PRN12345",
            "12345",
            "Department must contain at least one letter.",
        ),
    ],
)
def test_validate_student_rejects_invalid_details(
    name, prn, department, expected_error
):
    error = validate_student(name, prn, department)
    assert error == expected_error


def test_add_student_rejects_invalid_prn(client):
    login(client)

    response = client.post(
        "/students/add",
        data={
            "name": "Arya Student",
            "prn": "PRN@123",
            "department": "Computer Engineering",
        },
        follow_redirects=True,
    )

    assert (
        b"PRN can contain only letters, numbers, and internal hyphens."
        in response.data
    )
    assert b"Student added successfully." not in response.data
    
def test_unauthenticated_user_cannot_access(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 401, 403)
