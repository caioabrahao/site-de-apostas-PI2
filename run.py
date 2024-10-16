from flask import Flask, render_template, url_for, request, redirect, session
from flask_mail import Mail
from datetime import datetime
import oracledb
import uuid



#LEMBRETES:

# Fomatar a string de valores nas CONSULTAS SQL usando o TO_CHAR(<nome_da_coluna>, <tipo_de_formatacao>)
# exemplo: G = separador de milhar, D = separador de decimal, L adiciona o R$
# 1.000,00 = 999G999D00
# (Cuidado se for transformar a string em float ou int para calculos depois...)


# O módulo para criar chaves primárias é o UUID4 (exceto o id_user do usuário)
# O UUID4 gera strings de 36 caracteres.



# Função para criar conexão e cursor com DB Oracle
# Inserir as credencias de acordo com o DB criado
def connect_oracle(*nome_do_request):
    try:
        connection = oracledb.connect(user = 'projeto_integrador_user',
                                    password = 'pi1234',
                                    host = 'localhost',
                                    port= 1521,
                                    service_name = 'XEPDB1',
                                    )
    except Exception as error:
        print(f'Erro: {error}')
    else:
        print('Acesso ao Oracle com sucesso!')
        if nome_do_request != None:
            print(f'Requested by {nome_do_request[0]}')
    
    cursor = connection.cursor()
    
    return cursor, connection

# Função para formatar data do HTML (YYYY/MM/DD) para formato do Oracle (DD/MM/YYYY)
def format_date(date):

    input_date = date
    year = input_date[0:4]
    month = input_date[5:7]
    date = input_date[8:10]

    formatted_date = date + '-' + month + '-' + year
    
    return formatted_date

# Função para formatar objeto datetime em string do tipo DD/MM/YYYY
def format_datetime_to_string(objeto_datetime):

    objeto = objeto_datetime
    objeto_formatado = objeto.strftime("%d/%m/%Y")

    return objeto_formatado

# Essa função faz o SELECT do saldo do usuário já formatado na string com divisão de decimais e o insere/atualiza no session
# Como atualizar o saldo e algo que se repete, sempre chamar essa função
# o session["user_funds"] é uma string. Não usar o valor para calculos!!!! Para usar o saldo como calculo, faça um SELECT separadamente
def refresh_user_funds():

    cursor, connection = connect_oracle('refreshUserFunds')
    cursor.execute( """ SELECT TO_CHAR(saldo, '999G999G999D00')
                        FROM usuario
                        WHERE id_user = :id_user
                   
                    """,   
                        id_user = int(session.get("user_id")))
    
    funds = cursor.fetchone()
    funds = funds[0]

    session["user_funds"] = funds
    connection.close()

    return







app = Flask(__name__)


# Configurando o Flask-Mail
mail = Mail(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'sua_senha'
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@gmail.com'

# Chave secreta do Session
app.secret_key = "segredo"

@app.route('/')
def frontpage():

    return render_template('frontpage.html')

@app.route('/signUp', methods=['GET','POST'])
def cadastrar():

    # Função que calcula a idade inserida no campo HTML. Retorna True se idade for maior que 18. False se não.
    def calculate_age(date_string):
    
        input_date = date_string
        input_date = datetime.strptime(input_date, '%Y-%m-%d')
        today = datetime.now()

        delta_days = (today - input_date).days

        age = delta_days/365

        print(f'age = {age}')

        if age > 18:
            return True
        else:
            return False

    if request.method == 'GET':

        return render_template('signup.html')

    if request.method =='POST':
        
        # Informações Pessoais

        input_user_firstname = request.form.get('txtSignUp_Name')
        input_user_firstname.title()

        input_user_surname = request.form.get('txtSignUp_Surname')
        input_user_surname.title()

        input_user_cpf = request.form.get('txtSignUp_CPF')
        cursor, connection = connect_oracle('check_cpf')
        cursor.execute(f""" SELECT cpf_usuario FROM usuario WHERE cpf_usuario = '{input_user_cpf}' """)
        db_cpf_check = cursor.fetchone()

        if db_cpf_check != None:
            db_cpf_check = db_cpf_check[0]

        if input_user_cpf == db_cpf_check:
            valid_cpf = False
        else:
            valid_cpf = True
        connection.close()
       
        input_user_date = request.form.get('dateSignUp_Date')
        valid_age = calculate_age(input_user_date)
        input_user_date = format_date(input_user_date)
        
        input_user_phone = request.form.get('txtSignUp_Phone')

        # Informações de Endereço

        input_user_address_name = request.form.get('txtSignUp_AddressName')
        input_user_address_name = input_user_address_name.title()

        input_user_address_number = request.form.get('txtSignUp_AddressNumber')
        input_user_address_cep = request.form.get('txtSignUp_CEP')

        input_user_address_city = request.form.get('txtSignUp_City')
        input_user_address_city = input_user_address_city.title()

        input_user_address_state = request.form.get('txtSignUp_State')

        
        
        # Informações de Login
        
        input_user_email = request.form.get('emailSignUp_email')
        cursor, connection = connect_oracle('check_email')
        cursor.execute(f""" SELECT email_usuario FROM login WHERE email_usuario = '{input_user_email}' """)
        db_email_check = cursor.fetchone()

        if db_email_check != None:
            db_email_check = cursor.fetchone()[0]

        if input_user_email == db_email_check:
            valid_email = False
        else:
            valid_email = True

        input_user_password_1 = request.form.get('pwSignUp_password_1')
        input_user_password_2 = request.form.get('pwSignUp_password_2')

        if input_user_password_1 == input_user_password_2:
            valid_password = True
        else:
            valid_password = False

        # Tickboxes

        if request.form.get('checkboxSignUp_over18') == 'on':
            valid_checkbox_over18 = True
        else:
            valid_checkbox_over18 = False
        
        if request.form.get('checkboxSignUp_agree') == 'on':
            valid_checkbox_agree = True
        else:
            valid_checkbox_agree = False

        # Se não houver nenhum erro de input (se cpf, data de idade, email, senha e checkbox forem válidos), é feito o insert no BD.
        if all([valid_cpf, 
                valid_age,
                valid_email,
                valid_password, 
                valid_checkbox_over18, 
                valid_checkbox_agree]):
            try:
                cursor, connection = connect_oracle('singUP')
                cursor.execute(f"""INSERT INTO usuario  (id_user,
                                                        primeiro_nome,
                                                        sobrenome,
                                                        cpf_usuario,
                                                        telefone_usuario,
                                                        nome_endereco,
                                                        numero_endereco,
                                                        cep_endereco,
                                                        cidade_endereco,
                                                        uf_endereco
                                                        )
                                                        
                                    VALUES( seq_id_user.NEXTVAL,
                                    :input_user_firstname,
                                    :input_user_surname,
                                    :input_user_cpf,
                                    :input_user_phone,
                                    :input_user_address_name,
                                    :input_user_address_number,
                                    :input_user_address_cep,
                                    :input_user_address_city,
                                    '{input_user_address_state}'
                                    )

                                    """,
                                    input_user_firstname = input_user_firstname,
                                    input_user_surname = input_user_surname,
                                    input_user_cpf = input_user_cpf,
                                    input_user_phone = input_user_phone,
                                    input_user_address_name = input_user_address_name,
                                    input_user_address_number = input_user_address_number,
                                    input_user_address_cep = input_user_address_cep,
                                    input_user_address_city = input_user_address_city
                                    )

                cursor.execute(f"""INSERT INTO login    (id_user,
                                                        email_usuario,
                                                        senha_usuario,
                                                        user_type
                                                        )
                                
                                    VALUES( seq_id_user.CURRVAL,
                                            :input_user_email,
                                            :input_user_password_1,
                                            'USER'
                                          )
                                    """,
                                    input_user_email = input_user_email,
                                    input_user_password_1 = input_user_password_1)
                connection.commit()
                connection.close()

            except Exception as erro_oracle:
                
                print('Erro ao realizar Insert!')
                connection.rollback()
                connection.close()
                render_oracle_error = erro_oracle
                return render_template('signup.html',
                                       erro_oracle = render_oracle_error)   
            
            else: 
                return render_template('signup_success.html',
                                        user_firstname = input_user_firstname
                                      )

            
        # Caso algum erro seja acionado, a página é renderizada informando os erros de cadastro.
        else:
            return render_template('signup.html', 
                                   cpf_valido = valid_cpf,
                                   data_valida = valid_age,
                                   email_valido = valid_email,
                                   senha_valida = valid_password,
                                   checkbox_acima18_valido = valid_checkbox_over18,
                                   checkbox_aceitar_valido = valid_checkbox_agree)
  

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'GET':
        
        return render_template('login.html')


    if request.method == 'POST':
        input_username = request.form.get('txtUsername')
        input_password = request.form.get('txtPassword')

        cursor, connection = connect_oracle('login')
        cursor.execute(f""" SELECT email_usuario, 
                                   senha_usuario, 
                                   user_type,
                                   id_user 
                       
                            FROM login WHERE email_usuario = '{input_username}' 
                    """)
        db_select = cursor.fetchone()

        if db_select != None:
            db_username = db_select[0]
            db_password = db_select[1]
            db_usertype = db_select[2]
            db_user_id = db_select[3]
        else:
            db_username = None
            db_password = None
            db_usertype = None


        if (input_username == db_username) and (input_password == db_password):
            valid_login = True
            session["auth_user"] = 'usuario_autenticado'

            cursor.execute(f""" SELECT  primeiro_nome, 
                                        TO_CHAR(saldo, '999G999G999D00')  
                                FROM usuario WHERE id_user = {db_user_id} """)
            db_select = cursor.fetchone()

            db_user_firstname = db_select[0]
            db_user_funds = db_select[1]
            
            session["user_id"] = db_user_id
            session["user_type"] = db_usertype
            session["user_firstname"] = db_user_firstname
            session["user_funds"] = db_user_funds

            connection.close()

            return redirect(url_for('home'))
        else:
            valid_login = False
            return render_template('login.html',
                                   valid_login = valid_login)


@app.route('/logout')
def logout():
    
    session.clear()
    
    return redirect(url_for('frontpage'))

    
@app.route('/home', methods = ['GET'])
def home():
    
    if "auth_user" in session:


        return render_template("home.html",
                                user_firstname = session.get("user_firstname"),
                                user_funds = session.get("user_funds")
                              )
    else:
        return redirect(url_for('login'))
    

@app.route('/addNewEvent', methods=['GET','POST'])
def add_new_event():

    # Adicionar cota de aposta.

    if "auth_user" in session:
   
        if request.method == 'GET':

            return render_template("new_event.html",
                                    user_firstname = session.get("user_firstname"),
                                    user_funds = session.get("user_funds")
                                   )
        
        if request.method == 'POST':
            
            input_event_title = request.form.get("txt_titleName")
            input_event_description = request.form.get("txt_description")

            input_event_date = request.form.get("date_eventDate")
            formatted_event_date = format_date(input_event_date)
            
            input_event_category = request.form.get("txt_category")
            
            input_event_min_quota = request.form.get("txt_eventMinQuota")
            input_event_min_quota = float(input_event_min_quota)

            

            cursor, connection = connect_oracle('addNewEvent')
            generate_id_aposta = uuid.uuid4()

            try:    
                cursor.execute(f""" INSERT INTO aposta  (id_aposta,
                                                        id_user_author,
                                                        titulo,
                                                        descricao,
                                                        categoria,
                                                        data_evento,
                                                        quota_minima,
                                                        status       
                                                        )
                                
                                    VALUES  ('{generate_id_aposta}',
                                            {int(session.get("user_id"))},
                                            :input_event_title,
                                            :input_event_description,
                                            '{input_event_category}',
                                            TO_DATE('{formatted_event_date}', 'DD-MM-YYYY'),
                                            {input_event_min_quota},
                                            'APROVADO'
                                            )
                                    """,
                                    input_event_title = input_event_title,
                                    input_event_description = input_event_description)
            except Exception as erro:
                erro_oracle = erro
                new_event_success = False
                connection.rollback()
                connection.close()

            else:
                erro_oracle = None
                new_event_success = True
                connection.commit()
                connection.close()

            finally:
                return render_template("new_event_success.html",
                                        user_firstname = session.get("user_firstname"),
                                        user_funds = session.get("user_funds"),
                                        new_event_success = new_event_success,
                                        erro_insert_oracle = erro_oracle)

    else:
        return redirect(url_for('login'))    

# Rota para mecanismo de busca da Home

@app.route('/searchEvents', methods = ['GET','POST'])
def search_events():
    
    # Usar bind variables para evitar que um usuario execute comandos SQL mal intencionados (:<nome_variavel>:)
    # Documentação: https://cx-oracle.readthedocs.io/en/latest/user_guide/bind.html

    if "auth_user" in session:


        # Para formulários enviados através do GET deve-se usar o request.args e não o request.form !    
        input_search_event = request.args.get('txtInputSearchEvent')

        # O Oracle é case sensitive. Por padrão vamos tornar todas as strings minúsculas.
        input_search_event = input_search_event.lower()

        cursor, connection = connect_oracle('getEvents')

        lista_resultados = []

        class EventInfo():
            def __init__(self, event_id ,event_title, event_description, event_date) -> None:
                self.event_id = event_id
                self.title = event_title
                self.description = event_description
                self.event_date = event_date



        cursor.execute(""" SELECT COUNT (*) FROM APOSTA     WHERE ((LOWER(titulo) LIKE '%' || :input_search_event || '%')
                                                                OR (LOWER(categoria) LIKE '%' || :input_search_event || '%')
                                                                OR (LOWER(descricao) LIKE '%' || :input_search_event || '%'))
                           
                                                                AND STATUS = 'APROVADO' """, 
                       input_search_event = input_search_event)
        
        num_resultados = cursor.fetchone()
        print(num_resultados)
        num_resultados = num_resultados[0]

        if num_resultados != 0:
            
            no_results_found = False

            cursor.execute(""" SELECT * FROM aposta WHERE   ((LOWER(titulo) LIKE '%' || :input_search_event || '%')
                                                            OR (LOWER(categoria) LIKE '%' || :input_search_event || '%')
                                                            OR (LOWER(descricao) LIKE '%' || :input_search_event || '%'))
                           
                                                            AND STATUS = 'APROVADO' """, 
                           input_search_event = input_search_event)

            while True:
            
                linha = cursor.fetchone()
                print(linha)
                if linha == None:
                    break
                
                # A data do Oracle é recebida como objeto datetime. Usar função para formatar datetime para string.
                event_date = linha[5]
                formatted_event_date = event_date.strftime('%d/%m/%Y')
       
                event = EventInfo(event_id = linha[0],
                                event_title = linha[2],
                                event_description = linha[3],
                                event_date = formatted_event_date)
            
                lista_resultados.append(event)
        
        else:
            no_results_found = True


        connection.close()


        return render_template("search_events.html",
                                user_firstname = session.get("user_firstname"),
                                user_funds = session.get("user_funds"),
                                num_resultados = num_resultados,
                                lista_resultados = lista_resultados,
                                no_results_found = no_results_found)

    else:
        return redirect(url_for('login'))

@app.route('/betOnEvent/<event_id>', methods = ['GET', 'POST'])
def bet_on_event(event_id):

    class eventInfo():
        def __init__(self, event_title, event_description, event_category, event_date, event_date_starts, event_date_ends, event_minimum_quota, event_author_name) -> None:
            self.Title = event_title
            self.Description = event_description
            self.Category = event_category
            self.Date = event_date
            self.DateEventStarts = event_date_starts
            self.DateEventEnds = event_date_ends
            self.MinimumQuota = event_minimum_quota
            self.AuthorName = event_author_name
    
    event_id = event_id

    error_not_enough_funds = False
    error_below_quota = False
    error_no_option_chosen = True

    if "auth_user" in session:

        if request.method == 'GET':
            
            cursor, connection = connect_oracle('betOnEvent')
            
            # Consulta SQL para ver se o evento existe ou se foi aprovado
            # Se o evento não existe, o fetch retornará None
            # Nesses casos, a página de evento indisponível será renderizada

            cursor.execute("""  SELECT status 
                                FROM APOSTA 
                                WHERE id_aposta = :id_aposta """,
                            id_aposta = event_id)
            
            event_status = cursor.fetchone()
            event_status = event_status[0]
            event_status = event_status.strip()

            # Se o evento não existe
            if event_status == None:

                return render_template("unavaiable_event.html",
                                        user_firstname = session.get("user_firstname"),
                                        user_funds = session.get("user_funds"))
            
            # Se o evento não tiver o status 'APROVADO'.
            if event_status != "APROVADO":
                
                return render_template("unavaiable_event.html",
                                        user_firstname = session.get("user_firstname"),
                                        user_funds = session.get("user_funds"))
            
            # Fazer um template para evento já finalizado? As informações de aposta e qual resultado foi são mostradas
            

            # Tiradas essas exceções de evento não existir ou não ter sido aprovado, renderizamos a página do evento normalmente

            cursor.execute("""  SELECT  a.titulo,
                                        a.descricao,
                                        a.categoria,
                                        TO_CHAR(a.data_evento, 'DD/MM/YYYY'),
                                        TO_CHAR(a.data_inicio, 'DD/MM/YYYY'),
                                        TO_CHAR(a.data_termino,'DD/MM/YYYY'),
                                        a.quota_minima,
                                        u.primeiro_nome|| ' ' ||u.sobrenome
                                        

                                FROM aposta a
                                    INNER JOIN usuario u
                                        ON a.id_user_author = u.id_user
                
                                WHERE a.id_aposta = :id_aposta""",
                                id_aposta = event_id)

            event_select_db = cursor.fetchone()
            connection.close()

            evento = eventInfo( event_title = event_select_db[0],
                                event_description = event_select_db[1],
                                event_category = event_select_db[2],
                                event_date = event_select_db[3],
                                event_date_starts = event_select_db[4],
                                event_date_ends = event_select_db[5],
                                event_minimum_quota = event_select_db[6],
                                event_author_name = event_select_db[7]
                                )
            
            

            return render_template( "bet_on_event.html",
                                    user_firstname = session.get("user_firstname"),
                                    user_funds = session.get("user_funds"),
                                    event_id = event_id,
                                    evento = evento,
                                    error_not_enough_funds = error_not_enough_funds,
                                    error_below_quota = error_below_quota,
                                    confirm_event = False)
        

        if request.method == 'POST':
            

            #------------------ CÓDIGO DE APOSTA CONFIRMADA ----------------------------------

            # Aqui o html retorna true se o usuario passou por todo o fluxo e chegou na pagina de confimar aposta e confirmou.
            confirm_bet = request.form.get('confirm_bet')
            
            # Apos a confirmacao, aqui sao feitas as insercoes no BD.
            if confirm_bet == 'true':
                
                # Lembrar que usuario-aposta-transacao é uma relacao ternaria
                # Fazer o insert no transaction primeiro e depois o insert no usuarioAposta

                cursor, connection = connect_oracle('betonevent')
                id_transaction = uuid.uuid4()
                date_transaction = datetime.now()

                bet_value = float(session.get("user_bet_value"))
                transaction_value = -1*(bet_value)

                bet_option = session.get("user_bet_option")
                
                print(id_transaction, session.get("user_id"), event_id, date_transaction, transaction_value )
                print(type(date_transaction))

                # NAO PASSAR OBJETO DATETIME COM F-STRING. O SQL VAI ENTENDER QUE E UMA STRING E NAO UM DATETIME!!!
                # usar f-strings pra sql queries é dor de cabeça...
                try:
                    cursor.execute(f""" INSERT INTO transacao   (id_transaction,
                                                                id_user,
                                                                id_aposta,
                                                                date_transaction,
                                                                valor,
                                                                tipo)
                               
                                    VALUES                      ('{id_transaction}',
                                                                {int(session.get("user_id"))},
                                                                '{event_id}',
                                                                :date_transaction,
                                                                :transaction_value,
                                                                'SALDO EM APOSTA'
                                                                )
                                    """,                        
                                                                date_transaction = date_transaction,     
                                                                transaction_value = transaction_value)

                except Exception as erro_oracle:
                    print('betonEvent_Confirm ERRO: Primeiro insert em transacao')
                    connection.rollback()
                    connection.close()
                    erro_oracle = erro_oracle
                    return render_template("bet_on_event_fail.html",
                                            user_firstname = session.get("user_firstname"),
                                            user_funds = session.get("user_funds"),
                                            erro_oracle = erro_oracle)
                else:
                    connection.commit()
                
                try:
                    cursor.execute(f""" INSERT INTO usuarioAposta   (id_aposta,
                                                                    id_user,
                                                                    id_transaction,
                                                                    bet_value,
                                                                    bet_option)
                                   
                                        VALUES                      ('{event_id}',
                                                                    {int(session.get("user_id"))},
                                                                    '{id_transaction}',
                                                                    {bet_value},
                                                                    '{bet_option}'
                                                                    )
                                    """)
                except Exception as erro_oracle:
                    print('bet_on_event CONFIRM ERRO: Segundo insert em usuarioAposta')
                    connection.rollback()
                    connection.close()
                    erro_oracle = erro_oracle
                    return render_template("bet_on_event_fail.html",
                                            user_firstname = session.get("user_firstname"),
                                            user_funds = session.get("user_funds"),
                                            erro_oracle = erro_oracle)
                else:
                    connection.commit()
                
                # Como houve um insert na tabela transação, o trigger para atualizar o saldo foi acionado
                # Deve-se atualizar o valor de saldo da sessao

                connection.close()

                del session["user_bet_value"]
                del session["user_bet_option"]


                refresh_user_funds()

                return render_template("bet_on_event_success.html",
                                        user_firstname = session.get("user_firstname"),
                                        user_funds = session.get("user_funds"),
                                        id_transaction = id_transaction
                                       )

            #----------------------- FIM DO CÓDIGO DE APOSTA CONFIRMADA (aposta finalizada) --------------

            #----------------------- CÓDIGO DO INPUT DO USUÁRIO AO REALIZAR APOSTA -----------------------

            # O return do metodo get foi executado. As variaveis que receberam os dados consultados foram perdidos (poderia guardar no session...)
            # Fazer as consultas SQL novamente
            
            bet_value = request.form.get('bet_value')
            bet_option = request.form.get('bet_option')


            if bet_option == None:
                error_no_option_chosen = True
            else:
                error_no_option_chosen = False

            # Checar se o valor apostado não é maior do que o saldo em conta
            bet_value = float(bet_value)
            
            cursor, connection = connect_oracle('betOnEvent')
            cursor.execute(f""" SELECT saldo
                                FROM usuario
                                WHERE id_user = {int(session.get("user_id"))}
                                """)
            
            funds = cursor.fetchone()
            funds = funds[0]

            if bet_value > funds:
                error_not_enough_funds = True
            else:
                error_not_enough_funds = False

            cursor.execute("""  SELECT  a.titulo,
                                        a.descricao,
                                        a.categoria,
                                        TO_CHAR(a.data_evento, 'DD/MM/YYYY'),
                                        TO_CHAR(a.data_inicio, 'DD/MM/YYYY'),
                                        TO_CHAR(a.data_termino,'DD/MM/YYYY'),
                                        a.quota_minima,
                                        u.primeiro_nome|| ' ' ||u.sobrenome
                                        

                                FROM aposta a
                                    INNER JOIN usuario u
                                        ON a.id_user_author = u.id_user
                
                                WHERE a.id_aposta = :id_aposta
                                """,
                                id_aposta = event_id)
            
            event_select_db = cursor.fetchone()

            evento = eventInfo( event_title = event_select_db[0],
                                event_description = event_select_db[1],
                                event_category = event_select_db[2],
                                event_date = event_select_db[3],
                                event_date_starts = event_select_db[4],
                                event_date_ends = event_select_db[5],
                                event_minimum_quota = event_select_db[6],
                                event_author_name = event_select_db[7]
                                )

            if bet_value < evento.MinimumQuota:
                error_below_quota = True
            else:
                error_below_quota = False

            # Se houver não houver nenhum erro, o if not any é executado (todos são falsos). Se houver erro,
            # o else é executado com o template inicial e os erros acionados.
            if not any([error_no_option_chosen, error_not_enough_funds, error_below_quota]):

                session["user_bet_option"] = bet_option
                session["user_bet_value"] = bet_value

                return render_template("bet_on_event.html",
                                       user_firstname = session.get("user_firstname"),
                                       user_funds = session.get("user_funds"),
                                       event_id = event_id,
                                       evento = evento,
                                       bet_value = bet_value,
                                       bet_option = bet_option,
                                       confirm_event = True)
            
            else:
                return render_template("bet_on_event.html",
                                        user_firstname = session.get("user_firstname"),
                                        user_funds = session.get("user_funds"),
                                        event_id = event_id,
                                        evento = evento,
                                        error_no_option_chosen = error_no_option_chosen,
                                        error_not_enough_funds = error_not_enough_funds,
                                        error_below_quota = error_below_quota,
                                        confirm_event = False)
            
    else:
        return redirect(url_for('login'))

@app.route('/deleteEvent')
def delete_event():
    pass

@app.route('/evaluateNewEvent/<event_id>')
def evaluate_new_event(event_id):
    
    if "auth_user" in session and session.get("user_type") == 'MOD':
        event_id = event_id

    elif "auth_user" in session and session.get("user_type") == 'USER':
        return render_template("no_permission.html",
                                user_firstname = session.get("user_firstname"),
                                user_funds = session.get("user_funds"))

    else:
        return redirect(url_for('login'))


@app.route('/myWallet')
def my_wallet():
    
    if "auth_user" in session:

        return render_template("my_wallet.html",
                               user_firstname = session.get("user_firstname"),
                               user_funds = session.get("user_funds"))
    
    else:
        return redirect(url_for('login'))

@app.route('/addFunds')
def add_funds():
    
    if "auth_user" in session:

        return render_template("add_funds.html",
                                user_firstname = session.get("user_firstname"),
                                user_funds = session.get("user_funds"))
    else:
        return redirect(url_for('login'))

@app.route('/addFunds/creditCard', methods=['GET','POST'])
def add_funds_card():

    if "auth_user" in session:
        
        if request.method == 'GET':

            return render_template( "add_funds_card.html",
                                    user_firstname = session.get("user_firstname"),
                                    user_funds = session.get("user_funds"))
        
        if request.method == 'POST':
            
            
            deposit_value = request.form.get("radio_value")
            print(deposit_value)

            if deposit_value != 'other':
                deposit_value = float(deposit_value)
                valid_deposit_value = True
            else:

                # Colocar sistemas para checar o input do usuário. É melhor colocar no front?
                # Ex: Usuário pode inserir um texto no box, etc

                deposit_value = request.form.get("txt_input_value_other")
                valid_deposit_value = True
                if valid_deposit_value == True:
                    deposit_value = float(deposit_value)
                    deposit_value = round(deposit_value, 2)

                    if deposit_value < 0:
                        valid_deposit_value = False

            if valid_deposit_value == True:
                
                try:
                    cursor, connection = connect_oracle('add_funds')

                    id_transaction = uuid.uuid4()
                    date_transaction = datetime.now()

                    formatted_date = date_transaction.strftime("%d/%m/%Y %H:%M:%S")

                    cursor.execute(f""" INSERT INTO transacao   (id_transaction,
                                                                id_user,
                                                                date_transaction,
                                                                valor,
                                                                tipo
                                                                )
                                        
                                        VALUES                  ('{id_transaction}',
                                                                {int(session.get("user_id"))},
                                                                TO_DATE('{formatted_date}','DD-MM-YYYY HH24:MI:SS'),
                                                                {deposit_value},
                                                                'DEPÓSITO'
                                                                )
                             """)
                except Exception as erro_oracle:
                    erro_insert_oracle = erro_oracle
                    add_funds_success = False
                    connection.rollback()
                    connection.close()

                else:
                    
                    # Não há necessidade de atualizar o saldo
                    # O saldo já é atualizado por uma trigger criada no BD. Nome da trigger: atualizar_saldo_insert_transacao

                    add_funds_success = True
                    erro_insert_oracle = None
                    connection.commit()

                    # Atualizar novo saldo para o session
                    refresh_user_funds()

                finally:
                    return render_template( "add_funds_success.html",
                                            user_firstname = session.get("user_firstname"),
                                            user_funds = session.get("user_funds"),
                                            add_funds_success = add_funds_success,
                                            deposit_value = deposit_value,
                                            id_transaction = id_transaction,
                                            erro_insert_oracle = erro_insert_oracle
                                           )       
            else:
                return render_template("add_funds_card.html",
                                       valid_deposit_value = valid_deposit_value)
            
    else:
        return redirect(url_for('login'))

@app.route('/addFunds/pix')
def add_funds_pix():

    if "auth_user" in session:
        pass
    else:
        return redirect(url_for('login'))

@app.route('/withdrawFunds')
def withdraw_funds():
    if "auth_user" in session:

        render_template("withdraw_funds.html",
                        user_firstname = session.get("user_firstname"),
                        user_funds = session.get("user_funds"))
    
    else:
        return redirect(url_for('login'))

@app.route('/fundsHistory')
def funds_history():
    
    if "auth_user" in session:
        class TransactionInfo():
            def __init__(self, id_transaction, transaction_date, transaction_value, transaction_type) -> None:
                self.id_transaction = id_transaction
                self.date = transaction_date
                self.value = transaction_value
                self.type = transaction_type

        transactions_list = []

        cursor, connection = connect_oracle('fundsHistory')

        cursor.execute(f""" SELECT COUNT (*) 
                            FROM transacao 
                            WHERE id_user = {int(session.get("user_id"))} """)

        numero_linhas = cursor.fetchone()
        numero_linhas = numero_linhas[0]

        if numero_linhas != 0:

            no_transactions_found = False
            cursor.execute(f""" SELECT  id_transaction,
                                        date_transaction,
                                        TO_CHAR(valor, 'SL999G999G999D00'),
                                        tipo

                                FROM transacao 
                                WHERE id_user = {int(session.get("user_id"))} """)

            while True:

                linha = cursor.fetchone()
                if linha == None:
                    break

                transaction_date = linha[1]
                formatted_transaction_date = transaction_date.strftime('%d/%m/%Y %H:%M:%S')
                    
                transacao = TransactionInfo(id_transaction = linha[0],
                                            transaction_date = formatted_transaction_date,
                                            transaction_value = linha[2],
                                            transaction_type = linha[3])
                
                transactions_list.append(transacao)
                
        
        else:
            no_transactions_found = True
        
        connection.close()

        return render_template( "funds_history.html",
                                user_firstname = session.get("user_firstname"),
                                user_funds = session.get("user_funds"),
                                transactions = transactions_list,
                                numero_linhas = numero_linhas,
                                no_transactions_found = no_transactions_found)
    
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':

    app.run(debug=True)


