def enum(**enums: int):
    return type('Enum', (), enums)