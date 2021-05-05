def test_dict(other, user, host, password, database):
    print(f"{other}, {host}, {user}, {password}, {database}")

d = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "123456",
    "database": "test"
}

test_dict("other", **d)