from werkzeug.security import generate_password_hash

# Replace 'admin123' with the password you want to hash
password = 'admin123'
hash = generate_password_hash(password)

print("✅ Hashed password:\n", hash)
