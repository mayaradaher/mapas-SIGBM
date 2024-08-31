import warnings

import pandas as pd
import requests as r

from pandas import json_normalize

warnings.filterwarnings("ignore")

# Definindo URL base
url = "https://app.anm.gov.br/SIGBM/Publico/GerenciarPublico"

# Solicitando GET para obter os cookies
res = r.get(url, verify=False)
search_cookies = res.cookies

# Definindo dados de postagem
post_data = {
    "method": "POST",
    "startIndex": "0",
    "pageSize": "1000",
    "orderProperty": "TotalPontuacao",
    "orderAscending": "false",
    "DTOGerenciarFiltroPublico[CodigoBarragem]": "",
    "DTOGerenciarFiltroPublico[NecessitaPAEBM]": "0",
    "DTOGerenciarFiltroPublico[BarragemInseridaPNSB]": "0",
    "DTOGerenciarFiltroPublico[PossuiBackUpDam]": "0",
    "DTOGerenciarFiltroPublico[SituacaoDeclaracaoCondicaoEstabilidade]": "0",
}

# Solicitando POST com os dados e cookies
res_post = r.post(url, data=post_data, cookies=search_cookies, verify=False)

# Extraindo os valores do JSON
values = res_post.json()["Entities"]

# Criando um DataFrame com os valores
df = pd.json_normalize(values)

# Filtrando pelo município de Itabira
municipality_itabira = "ITABIRA"
df_municipality = df[df["Municipio"] == municipality_itabira]

# Separando os nomes das barragens ("NomeBarragem")
barragem = df_municipality["NomeBarragem"]

# Separando as chaves
keys = df_municipality["Chave"]

# Separando os id_barragem ("Codigo") para juntar com os dados exportados do Excel SIGBM
id_barragem = df_municipality["Codigo"]

# Juntando com os dados exportados do Excel SIGBM
df_municipality_key = pd.DataFrame({"Chave": keys, "ID Barragem": id_barragem})

# Separando os ids ("CodigoDeclaracaoAtual")
ids = df_municipality["CodigoDeclaracaoAtual"]

# Juntando com os dados exportados do Excel SIGBM
df_municipality_id = pd.DataFrame(
    {"NomeBarragem": barragem, "ID": ids, "ID Barragem": id_barragem}
)
