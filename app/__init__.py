from flask import Flask
import cx_Oracle
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuração da conexão com o banco de dados Oracle
    try:
        cx_Oracle.init_oracle_client(lib_dir=r"C:\caminho\para\instantclient_19_8")  # Confirmem o caminho que baixaram
        connection = cx_Oracle.connect(
            user=app.config['ORACLE_USER'],
            password=app.config['ORACLE_PASSWORD'],
            dsn=app.config['ORACLE_DSN']
        )
        app.config['db_connection'] = connection
    except Exception as e:
        print("Erro ao conectar ao Oracle Database: ", e)
        exit(1)

    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app