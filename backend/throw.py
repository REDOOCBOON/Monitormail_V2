from werkzeug.security import generate_password_hash
print(generate_password_hash("ujjwal@123", method='pbkdf2:sha256'))