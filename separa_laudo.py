import logging
import os
import re
import requests
from pypdf import PdfReader, PdfWriter
 
logging.getLogger("pypdf").setLevel(logging.ERROR)
 
ARQUIVO = r"D:\Arquivos PY\Repositorio-P0\Laudos\Exemplo_LAB_B_3L_3N.pdf"
PASTA_SAIDA = r"D:\Arquivos PY\Repositorio-P0\Laudos_Separados"
MODELO = "qwen2.5:3b"
 
# Cria a pasta de saída automaticamente caso ela ainda não exista
os.makedirs(PASTA_SAIDA, exist_ok=True)
 
#Envia as instruções e o o texto da página para a IA identificar o código do laudo
def identificar_codigo(texto):
    prompt = f"""Sua tarefa é varrer TODO o texto abaixo e localizar a sequência desejada, mesmo que ela esteja no meio de uma frase, dentro de uma tabela ou junto de outras palavras.
    
    A sequência segue obrigatoriamente um destes três formatos:
    Formato 1: "2 letras maiúsculas" + "_" + "3 números" (Exemplo: XY_123)
    Formato 2: "3 letras maiúsculas" + "_" + "3 números" (Exemplo: XYZ_123)
    Formato 3: "3 letras maiúsculas" + "_" + "4 números" (Exemplo: XYZ_0123)
    
    Regras:
    1. Leia cada linha com atenção, procurando o caractere "_" cercado por letras maiúsculas à esquerda e 3 ou 4 dígitos à direita.
    2. A sequência pode estar isolada em uma linha ou no meio de uma frase/tabela junto com outras palavras.
    3. Copie EXATAMENTE a sequência que aparece escrita no texto. NUNCA invente sequência ou utilize a sequência do exemplo fictício acima.
    4. Responda APENAS com a sequência encontrada, sem frases ou explicações.
    5. Somente se não encontrar uma sequência em nenhum desses formatos em todo o texto, responda NAO_ENCONTRADO.
    
    Texto:
    {texto}
    """
    
    resposta = requests.post("http://127.0.0.1:11434/api/generate",
                             json={"model": MODELO,
                                   "prompt": prompt,
                                   "stream": False,
                                   "think": False,
                                   "options": {"temperature": 0.0,
                                               "num_predict": 10}

                                  },
                             timeout=300
                            )
    
    return resposta.json()["response"].strip()


# Remove quebras de linha caso o modelo envie texto extra e limpa caracteres inválidos
def limpar_nome(codigo):
    codigo = codigo.splitlines()[0].strip()
    return re.sub(r'[\\/:*?"<>|]', "_", codigo)
 
 
reader = PdfReader(ARQUIVO)
 
laudos = {}
codigo_atual = None
 
 
for numero_pagina, pagina in enumerate(reader.pages):
 
    texto = pagina.extract_text() or ""
    texto = texto.replace("/", " ")
    texto = texto[:500] # Para limitar o texto que será analizado pela IA
    #print(f"Texto enviado: {texto}") # Utilizado para checagem do texto cortado
    print(f"Página {numero_pagina + 1} enviada à IA")
    
    codigo = identificar_codigo(texto)

    print(f"Página {numero_pagina + 1}: {codigo}")

    # Se encontrou um código, considera que a página pertence a esse laudo.
    if codigo != "NAO_ENCONTRADO":
        codigo_atual = limpar_nome(codigo)
    
    # Se não encontrou código, considera continuação do laudo anterior.
    if codigo_atual is not None:
        if codigo_atual not in laudos:
            laudos[codigo_atual] = []
        laudos[codigo_atual].append(numero_pagina)
 
 
# Criação dos PDFs individuais
for codigo, paginas in laudos.items():
    
    writer = PdfWriter()
    
    for numero_pagina in paginas:
        writer.add_page(reader.pages[numero_pagina])
    
    nome_arquivo = os.path.join(PASTA_SAIDA, f"{codigo.upper()}.pdf")
    
    with open(nome_arquivo, "wb") as arquivo_saida:
        writer.write(arquivo_saida)
    
    print(f"Salvo: {nome_arquivo}")
    
    
print("\nProcessamento concluído.")