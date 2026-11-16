"""
Script para gerar dados_exemplo.json, popular o CSV inicial e criar arquivos de teste.
"""
import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados", "recibos")
DIGITALIZADOS_DIR = os.path.join(DADOS_DIR, "digitalizados")

os.makedirs(DIGITALIZADOS_DIR, exist_ok=True)

REGISTROS_EXEMPLO = [
    {
        "numero": 1,
        "numerador_completo": "001/2026",
        "data_elaboracao": "10/01/2026",
        "horario_elaboracao": "09:30:00",
        "gerador_posto": "Coordenador",
        "gerador_re": "10001-X",
        "gerador_nome": "FULANO DE TAL",
        "gerador_completo": "Coordenador 10001-X FULANO DE TAL",
        "gerador_unidade": "Unidade Exemplo – Setor de Logística",
        "recebedor_posto": "Analista",
        "recebedor_re": "20002-Y",
        "recebedor_nome": "CICLANO DA SILVA",
        "recebedor_completo": "Analista 20002-Y CICLANO DA SILVA",
        "recebedor_unidade": "Unidade Exemplo – Setor A",
        "destinatario": "Unidade Exemplo – Setor A",
        "assunto": "MATERIAL DE ESCRITÓRIO E INFORMÁTICA",
        "descricao_itens": "[TABELA: MATERIAIS DE ESCRITÓRIO]\n05 | RESMAS DE PAPEL SULFITE A4\n02 | TONERS PARA IMPRESSORA LASER\n10 | CANETAS ESFEROGRÁFICAS AZUIS",
        "status_assinatura": "Assinado",
        "nome_arquivo": "1.MATERIAL DE ESCRITORIO E INFORMATICA Analista 20002-Y CICLANO DA SILVA.pdf",
        "caminho_arquivo": os.path.join("dados", "recibos", "digitalizados", "1.MATERIAL DE ESCRITORIO E INFORMATICA Analista 20002-Y CICLANO DA SILVA.pdf").replace("\\", "/"),
        "data_upload": "10/01/2026 14:30:00"
    },
    {
        "numero": 2,
        "numerador_completo": "002/2026",
        "data_elaboracao": "15/01/2026",
        "horario_elaboracao": "11:15:00",
        "gerador_posto": "Assistente",
        "gerador_re": "10003-Z",
        "gerador_nome": "BELTRANO SOUZA",
        "gerador_completo": "Assistente 10003-Z BELTRANO SOUZA",
        "gerador_unidade": "Unidade Exemplo – Setor de Logística",
        "recebedor_posto": "Técnico",
        "recebedor_re": "20004-W",
        "recebedor_nome": "MARIA OLIVEIRA",
        "recebedor_completo": "Técnico 20004-W MARIA OLIVEIRA",
        "recebedor_unidade": "Unidade Exemplo – Setor B",
        "destinatario": "Unidade Exemplo – Setor B",
        "assunto": "EQUIPAMENTOS DE PROTEÇÃO INDIVIDUAL (EPI)",
        "descricao_itens": "[TABELA: EQUIPAMENTOS DE SEGURANÇA]\n04 | CAPACETES DE SEGURANÇA BRANCOS\n04 | ÓCULOS DE PROTEÇÃO TRANSPARENTES\n08 | PARES DE LUVAS DE VAQUETA",
        "status_assinatura": "pendencia de assinatura",
        "nome_arquivo": "",
        "caminho_arquivo": "",
        "data_upload": ""
    },
    {
        "numero": 3,
        "numerador_completo": "003/2026",
        "data_elaboracao": "01/02/2026",
        "horario_elaboracao": "14:00:00",
        "gerador_posto": "Coordenador",
        "gerador_re": "10001-X",
        "gerador_nome": "FULANO DE TAL",
        "gerador_completo": "Coordenador 10001-X FULANO DE TAL",
        "gerador_unidade": "Unidade Exemplo – Setor de Logística",
        "recebedor_posto": "Supervisor",
        "recebedor_re": "20005-K",
        "recebedor_nome": "JOSÉ SANTOS",
        "recebedor_completo": "Supervisor 20005-K JOSÉ SANTOS",
        "recebedor_unidade": "Unidade Exemplo – Setor C",
        "destinatario": "Unidade Exemplo – Setor C",
        "assunto": "FERRAMENTAS E ACESSÓRIOS DE MANUTENÇÃO",
        "descricao_itens": "01 (UM) JOGO DE CHAVES COMBINADAS DE 6MM A 22MM.\n01 (UM) MULTÍMETRO DIGITAL COM PONTAS DE PROVA.\n02 (DOIS) ROLOS DE FITA ISOLANTE.",
        "status_assinatura": "Assinado",
        "nome_arquivo": "3.FERRAMENTAS E ACESSORIOS DE MANUTENCAO Supervisor 20005-K JOSE SANTOS.pdf",
        "caminho_arquivo": os.path.join("dados", "recibos", "digitalizados", "3.FERRAMENTAS E ACESSORIOS DE MANUTENCAO Supervisor 20005-K JOSE SANTOS.pdf").replace("\\", "/"),
        "data_upload": "01/02/2026 16:45:12"
    },
    {
        "numero": 4,
        "numerador_completo": "004/2026",
        "data_elaboracao": "10/02/2026",
        "horario_elaboracao": "16:20:00",
        "gerador_posto": "Assistente",
        "gerador_re": "10003-Z",
        "gerador_nome": "BELTRANO SOUZA",
        "gerador_completo": "Assistente 10003-Z BELTRANO SOUZA",
        "gerador_unidade": "Unidade Exemplo – Setor de Logística",
        "recebedor_posto": "",
        "recebedor_re": "",
        "recebedor_nome": "",
        "recebedor_completo": "",
        "recebedor_unidade": "Unidade Exemplo – Operações",
        "destinatario": "Unidade Exemplo – Operações",
        "assunto": "RETIRADA DE MATERIAIS DE CONSUMO",
        "descricao_itens": "[TABELA: MATERIAIS DE CONSUMO]\n10 | CAIXAS DE COPOS DESCARTÁVEIS 200ML\n05 | PACOTES DE CAFÉ 500G\n10 | PACOTES DE AÇÚCAR 1KG",
        "status_assinatura": "pendencia de assinatura",
        "nome_arquivo": "",
        "caminho_arquivo": "",
        "data_upload": ""
    }
]

# 1. Salvar dados_exemplo.json
caminho_json = os.path.join(BASE_DIR, "dados_exemplo.json")
with open(caminho_json, "w", encoding="utf-8") as f:
    json.dump(REGISTROS_EXEMPLO, f, indent=4, ensure_ascii=False)
print(f"✅ Criado: {caminho_json}")

# 2. Salvar CSV inicial
caminho_csv = os.path.join(DADOS_DIR, "controle_recibos.csv")
df = pd.DataFrame(REGISTROS_EXEMPLO)
df.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
print(f"✅ Criado: {caminho_csv}")

# 3. Criar PDFs fictícios de exemplo para os recibos assinados (Recibo 1 e Recibo 3)
pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"

for reg in REGISTROS_EXEMPLO:
    if reg["status_assinatura"] == "Assinado" and reg["nome_arquivo"]:
        caminho_pdf = os.path.join(DIGITALIZADOS_DIR, reg["nome_arquivo"])
        with open(caminho_pdf, "wb") as f_pdf:
            f_pdf.write(pdf_content)
        print(f"✅ Criado PDF mock: {caminho_pdf}")

print("\n🚀 Todos os dados de exemplo foram gerados com sucesso!")

