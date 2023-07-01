import hashlib
import clize
import boto3


def compute_password(username: str, secret_seed: str) -> str:
    m = hashlib.sha256()
    m.update(username.encode())
    m.update(secret_seed.encode())
    d = m.hexdigest()
    return d

