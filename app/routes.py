from flask import Blueprint, request, jsonify, current_app
import cx_Oracle
import jwt
import datetime

bp = Blueprint('routes', __name__)

# Serviço de Cadastro (/signUp)
@bp.route('/signUp', methods=['POST'])
def sign_up():
    data = request.json
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    data_nascimento = data.get('data_nascimento')

    if not nome or not email or not senha or not data_nascimento:
        return jsonify({"message": "Todos os campos são obrigatórios"}), 400

    connection = current_app.config['db_connection']
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha, data_nascimento)
            VALUES (:nome, :email, :senha, TO_DATE(:data_nascimento, 'YYYY-MM-DD'))
        """, [nome, email, senha, data_nascimento])
        connection.commit()
        return jsonify({"message": "Usuário cadastrado com sucesso!"}), 201
    except cx_Oracle.Error as error:
        print("Erro ao cadastrar usuário: ", error)
        return jsonify({"message": "Erro ao cadastrar usuário"}), 500
    finally:
        cursor.close()

# Serviço de Login (/login)
@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')

    if not email or not senha:
        return jsonify({"message": "Email e senha são obrigatórios"}), 400

    connection = current_app.config['db_connection']
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT id, nome FROM usuarios WHERE email=:email AND senha=:senha
        """, [email, senha])
        user = cursor.fetchone()

        if user:
            token = jwt.encode({
                'user_id': user[0],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, current_app.config['SECRET_KEY'])
            return jsonify({"token": token}), 200
        else:
            return jsonify({"message": "Credenciais inválidas"}), 401
    except cx_Oracle.Error as error:
        print("Erro ao realizar login: ", error)
        return jsonify({"message": "Erro ao realizar login"}), 500
    finally:
        cursor.close()

# Serviço de Criação de Eventos (/addNewEvent)
@bp.route('/addNewEvent', methods=['POST'])
def add_new_event():
    data = request.json
    titulo = data.get('titulo')
    descricao = data.get('descricao')
    valor_cota = data.get('valor_cota')
    data_inicio = data.get('data_inicio')
    data_fim = data.get('data_fim')
    data_evento = data.get('data_evento')

    if not all([titulo, descricao, valor_cota, data_inicio, data_fim, data_evento]):
        return jsonify({"message": "Todos os campos são obrigatórios"}), 400

    connection = current_app.config['db_connection']
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO eventos (titulo, descricao, valor_cota, data_inicio, data_fim, data_evento)
            VALUES (:titulo, :descricao, :valor_cota, TO_DATE(:data_inicio, 'YYYY-MM-DD'), TO_DATE(:data_fim, 'YYYY-MM-DD'), TO_DATE(:data_evento, 'YYYY-MM-DD'))
        """, [titulo, descricao, valor_cota, data_inicio, data_fim, data_evento])
        connection.commit()
        return jsonify({"message": "Evento criado com sucesso!"}), 201
    except cx_Oracle.Error as error:
        print("Erro ao criar evento: ", error)
        return jsonify({"message": "Erro ao criar evento"}), 500
    finally:
        cursor.close()

# Serviço de Listagem de Eventos (/getEvents)
@bp.route('/getEvents', methods=['GET'])
def get_events():
    status = request.args.get('status')

    connection = current_app.config['db_connection']
    cursor = connection.cursor()

    try:
        if status == 'aguardando_aprovacao':
            cursor.execute("SELECT * FROM eventos WHERE status='PENDENTE'")
        elif status == 'ocorridos':
            cursor.execute("SELECT * FROM eventos WHERE status='OCORRIDO'")
        else:
            cursor.execute("SELECT * FROM eventos WHERE status='FUTURO'")

        eventos = cursor.fetchall()
        eventos_list = [{"id": row[0], "titulo": row[1], "descricao": row[2]} for row in eventos]
        return jsonify(eventos_list), 200
    except cx_Oracle.Error as error:
        print("Erro ao buscar eventos: ", error)
        return jsonify({"message": "Erro ao buscar eventos"}), 500
    finally:
        cursor.close()

        # Serviço de Aprovação de Eventos (/evaluateNewEvent)
@bp.route('/evaluateNewEvent', methods=['POST'])
def evaluate_new_event():
    data = request.json
    evento_id = data.get('evento_id')
    aprovado = data.get('aprovado')
    motivo_rejeicao = data.get('motivo_rejeicao', '')

    if not evento_id or aprovado is None:
        return jsonify({"message": "Evento ID e status de aprovação são obrigatórios"}), 400

    connection = current_app.config['db_connection']
    cursor = connection.cursor()

    try:
        if aprovado:
            cursor.execute("UPDATE eventos SET status='APROVADO' WHERE id=:evento_id", [evento_id])
        else:
            cursor.execute("UPDATE eventos SET status='REJEITADO', motivo_rejeicao=:motivo_rejeicao WHERE id=:evento_id", [evento_id, motivo_rejeicao])
        connection.commit()
        return jsonify({"message": "Evento avaliado com sucesso!"}), 200
    except cx_Oracle.Error as error:
        print("Erro ao avaliar evento: ", error)
        return jsonify({"message": "Erro ao avaliar evento"}), 500
    finally:
        cursor.close()

# Serviço de Apostas (/betOnEvent)
@bp.route('/betOnEvent', methods=['POST'])
def bet_on_event():
    data = request.json
    evento_id = data.get('evento_id')
    valor = data.get('valor')
    aposta_sim = data.get('aposta_sim')

    if not evento_id or not valor ou aposta_sim is None:
        return jsonify({"message": "Evento ID, valor da aposta e tipo de aposta são obrigatórios"}), 400

    connection = current_app.config['db_connection']
    cursor = connection.cursor()

    try:
        # Verificar saldo e deduzir aposta
        cursor.execute("SELECT saldo FROM usuarios WHERE id=:user_id", [user_id])
        saldo = cursor.fetchone()[0]

        if saldo < valor:
            return jsonify({"message": "Saldo insuficiente"}), 400

        cursor.execute("""
            INSERT INTO apostas (evento_id, user_id, valor, aposta_sim)
            VALUES (:evento_id, :user_id, :valor, :aposta_sim)
        """, [evento_id, user_id, valor, aposta_sim])
        
        cursor.execute("UPDATE usuarios SET saldo=saldo-:valor WHERE id=:user_id", [valor, user_id])
        connection.commit()
        return jsonify({"message": "Aposta realizada com sucesso!"}), 201
    except cx_Oracle.Error as error:
        print("Erro ao realizar aposta: ", error)
        return jsonify({"message": "Erro ao realizar aposta"}), 500
    finally:
        cursor.close()

# Serviço de Finalização de Evento (/finishEvent)
@bp.route('/finishEvent', methods=['POST'])
def finish_event():
    data = request.json
    evento_id = data.get('evento_id')
    ocorreu = data.get('ocorreu')

    if not evento_id ou ocorreu is None:
        return jsonify({"message": "Evento ID e resultado são obrigatórios"}), 400

    connection = current_app.config['db_connection']
    cursor = connection.cursor()

    try:
        # Atualizar status do evento
        cursor.execute("UPDATE eventos SET status='OCORRIDO', ocorreu=:ocorreu WHERE id=:evento_id", [ocorreu, evento_id])

        # Distribuir ganhos
        if ocorreu:
            cursor.execute("""
                SELECT user_id, valor FROM apostas WHERE evento_id=:evento_id AND aposta_sim=:aposta_sim
            """, [evento_id, True])
        else:
            cursor.execute("""
                SELECT user_id, valor FROM apostas WHERE evento_id=:evento_id AND aposta_sim=:aposta_sim
            """, [evento_id, False])

        apostas_vencedoras = cursor.fetchall()

        for aposta in apostas_vencedoras:
            cursor.execute("""
                UPDATE usuarios SET saldo=saldo+:valor WHERE id=:user_id
            """, [aposta[1], aposta[0]])

        connection.commit()
        return jsonify({"message": "Evento finalizado e ganhos distribuídos!"}), 200
    except cx_Oracle.Error as error:
        print("Erro ao finalizar evento: ", error)
        return jsonify({"message": "Erro ao finalizar evento"}), 500
    finally:
        cursor.close()

# Serviço de Busca de Eventos (/searchEvent)
@bp.route('/searchEvent', methods=['GET'])
def search_event():
    keyword = request.args.get('keyword', '')

    connection = current_app.config['db_connection']
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT id, titulo, descricao FROM eventos WHERE titulo LIKE '%' || :keyword || '%' OR descricao LIKE '%' || :keyword || '%'
        """, [keyword])

        eventos = cursor.fetchall()
        eventos_list = [{"id": row[0], "titulo": row[1], "descricao": row[2]} for row in eventos]
        return jsonify(eventos_list), 200
    except cx_Oracle.Error as error:
        print("Erro ao buscar eventos: ", error)
        return jsonify({"message": "Erro ao buscar eventos"}), 500
    finally:
        cursor.close()
