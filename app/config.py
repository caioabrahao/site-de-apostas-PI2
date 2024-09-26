import os

class Config:
    ORACLE_USER = os.getenv('ORACLE_USER', 'seu_usuario_oracle')
    ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', 'sua_senha_oracle')
    ORACLE_DSN = os.getenv('ORACLE_DSN', 'XXX')  # Modifique conforme necessário
    SECRET_KEY = os.getenv('SECRET_KEY', 'XXX')
