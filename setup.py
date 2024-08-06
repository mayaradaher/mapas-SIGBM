import os
import pandas as pd
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mapas_inundacao import page

# Caminhos dos arquivos
previous_file = "data/data_previous.xlsx"
current_file = "data/data_today.xlsx"

# Carregando dados do dia anterior
if os.path.exists(previous_file):
    df_previous = pd.read_excel(previous_file)
else:
    df_previous = pd.DataFrame()

df_previous = df_previous.fillna("")

# Salvando dados de hoje
page.df_page.to_excel(current_file, index=False)

# Carregando dados de hoje
df_today = pd.read_excel(current_file)

# Limpando os NAs
df_today = df_today.fillna("")

# Armazenando as barragens com novas colunas preenchidas
barragens_com_novas_colunas = {}

# Iterando pelas colunas CodigoMapa
codigo_mapa_columns = [col for col in df_today.columns if col.startswith("CodigoMapa")]

for col in codigo_mapa_columns:
    for index, row in df_today.iterrows():
        id_barragem = row["ID Barragem"]
        if id_barragem in df_previous["ID Barragem"].values:
            previous_value = df_previous[df_previous["ID Barragem"] == id_barragem][col].values[0]
            current_value = row[col]
            # Verificando se a coluna estava vazia no df_previous e se agora tem um valor
            if previous_value == "" and current_value != "":
                barragem = row["NomeBarragem"]
                if barragem not in barragens_com_novas_colunas:
                    barragens_com_novas_colunas[barragem] = []
                barragens_com_novas_colunas[barragem].append(col)

print("Barragens com novas colunas preenchidas:", barragens_com_novas_colunas)

# Configurando servidor SMTP
server_smtp = "smtp.gmail.com"
port = 587
sender_email = os.getenv("SENDER_EMAIL")
password = os.getenv("PASSWORD_EMAIL")
receive_email = os.getenv("RECEIVE_EMAIL")
subject = "Mapa de Inundação adicionado"

# Enviando e-mail se houver novas colunas
if barragens_com_novas_colunas:
    body_lines = []
    for barragem, colunas in barragens_com_novas_colunas.items():
        body_lines.append(
            f"• Barragem <b>{barragem}</b> teve um novo Mapa de Inundação adicionado."
        )

    body = "<br>".join(body_lines)

    # Criando o e-mail
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receive_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    # Conectando o servidor SMTP
    try:
        server = smtplib.SMTP(server_smtp, port)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receive_email, msg.as_string())
        print("E-mail enviado com sucesso")
    except Exception as e:
        print(f"Houve algum erro: {e}")
    finally:
        server.quit()

# Substituindo o arquivo do dia anterior pelo de hoje
os.replace(current_file, previous_file)
