COMMON_PASSWORDS = {
    "admin123",
    "password",
    "password123",
    "12345678",
    "qwerty123",
}


def password_strength_error(password):
    if not password or len(password) < 8:
        return "La clave debe tener al menos 8 caracteres."
    if password.strip() != password:
        return "La clave no puede empezar ni terminar con espacios."
    if password.lower() in COMMON_PASSWORDS:
        return "La clave es demasiado comun."
    if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
        return "La clave debe combinar letras y numeros."
    return None


def validate_password_strength(password):
    error = password_strength_error(password)
    if error:
        raise ValueError(error)
    return password
