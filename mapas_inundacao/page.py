import time
import warnings
from collections import Counter

import pandas as pd
import requests as r
import re
from bs4 import BeautifulSoup
from requests.exceptions import ConnectTimeout

from . import key_id

warnings.filterwarnings("ignore")


def scrap_id_info(id: str) -> dict:
    print(f"{id} Extraindo dados Mapas de Inundação...")
    id_url = f"https://app.anm.gov.br/SIGBM/MapaDeInundacaoPublico/BuscarPartial?idDeclaracao={id}"

    for attempt in range(5):  # Número máximo de tentativas
        try:
            page = r.get(id_url, timeout=12, verify=False)  # Tempo limite
            page.raise_for_status()  # Verifica se a solicitação teve sucesso
            break  # Se bem-sucedido, saia do loop de tentativas
        except (ConnectTimeout, r.exceptions.RequestException):
            if attempt < 5 - 1:
                print(
                    f"Tentativa {attempt + 1} falhou. Tentando novamente após 5 segundos..."
                )
                time.sleep(5)  # Atraso entre as tentativas em segundos
            else:
                print(f"Atingiu o número máximo de tentativas para {id}.")
                return None  # Retorna None se as tentativas falharem

    soup = BeautifulSoup(page.content, "html.parser")

    # Regex para capturar nomes em JavaScript
    tag1 = soup.find_all("script", {"type": "text/javascript"})[0].text
    name_pattern = re.compile(r'((?<=CodigoMapa":")(.*?)")', flags=re.M)
    tag1 = name_pattern.findall(tag1)
    id_dict = {("CodigoMapa"): tag1 for tag in tag1}

    dict = {**id_dict}

    dict["ID"] = id

    return dict


# Obtendo as informações acima, agora para todas as barragens
id_page = [scrap_id_info(id) for id in key_id.ids]

# Limpando os dados
df_page = pd.DataFrame(id_page)

# Verificando se o parâmetro "CodigoMapa" existe na página
if "CodigoMapa" in df_page.columns:
    df_page["CodigoMapa"] = df_page["CodigoMapa"].apply(
        lambda x: re.sub(r'"', "", re.sub(r"[,\[\]()\\]", "", str(x)))
    )


# Removendo blocos duplicados que vieram do javascript (parâmetro "CodigoMapa")
def remove_repeated_blocks(text):
    blocks = text.split("'")
    block_counts = Counter(blocks)
    result_blocks = []

    for block in blocks:
        block = block.strip()
        if block_counts[block] == 1:
            result_blocks.append(block)
        elif block not in result_blocks:
            result_blocks.append(block)

    # Remover o bloco vazio se ele estiver no início
    if result_blocks and result_blocks[0] == "":
        result_blocks.pop(0)

    return " ".join([f"'{block}'" for block in result_blocks])


df_page["CodigoMapa"] = df_page["CodigoMapa"].apply(remove_repeated_blocks)

# Separando a coluna 'CodigoMapa' em múltiplas colunas
df_page["CodigoMapa"] = df_page["CodigoMapa"].str.split(" ")

# Encontrando o número máximo de elementos em 'CodigoMapa'
max_len = df_page["CodigoMapa"].apply(len).max()

# Criando novas colunas para cada elemento de 'CodigoMapa'
for i in range(max_len):
    df_page[f"CodigoMapa_{i+1}"] = df_page["CodigoMapa"].apply(
        lambda x: x[i] if i < len(x) else None
    )

# Removendo a coluna original 'CodigoMapa'
df_page.drop(columns=["CodigoMapa"], inplace=True)

df_page = pd.merge(df_page, key_id.df_municipality_id, how="inner", on="ID")

# Selecionando colunas para exibição final
final_columns = ["ID Barragem", "NomeBarragem"] + [
    f"CodigoMapa_{i+1}" for i in range(max_len)
]
df_page = df_page[final_columns]
