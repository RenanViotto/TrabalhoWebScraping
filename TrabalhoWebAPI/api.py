from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import json

def Buscar_dados(categoria_escolhida):
    # Simula navegador
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # Lista vazia onde os produtos serão guardados
    produtos_encontrados = []
    
    # URL da página inicial do site
    url_principal = "https://scrapingsandbox.com/"
    
    try:
        # Faz a requisição HTTP (baixa o HTML da página)
        resposta = requests.get(url_principal, headers=headers, timeout=10)
        
        # Só continua se o site responder com sucesso (status 200)
        if resposta.status_code == 200:
            # Transforma o HTML bruto em algo que o Python consegue navegar
            soup = BeautifulSoup(resposta.text, "html.parser")
            
            # Encontra todos os cards de produto na página
            cards = soup.find_all("a", class_="product-card")
            
            # Para cada card encontrado, extrai as informações
            for card in cards:
                # Procura a tag que contém a categoria
                categoria_tag = card.find("span", class_="category")
                # Se achou, pega o texto; se não, deixa vazio
                categoria_site = categoria_tag.get_text(strip=True) if categoria_tag else ""

                # FILTRO: Só processa se a categoria do produto for igual à escolhida
                if categoria_site.lower() == categoria_escolhida.lower():
                    # Procura a tag do nome, preço e avaliação
                    nome_tag = card.find("h3", class_="product-name")
                    preco_tag = card.find("span", class_="price")
                    avaliacao_tag = card.find("span", class_="rating")
                    # Pega o link (href) do produto
                    href = card.get("href")

                    # Se o link existir, adiciona o produto na lista
                    if href:
                        produtos_encontrados.append({
                            # Pega o texto da tag ou define um padrão caso ela não exista
                            "nome": nome_tag.get_text(strip=True) if nome_tag else "Sem nome",
                            "preco": preco_tag.get_text(strip=True) if preco_tag else "Sem preço",
                            "categoria": categoria_site,
                            "avaliacao": avaliacao_tag.get_text(strip=True) if avaliacao_tag else "Sem avaliação",
                            # Monta o link completo do produto
                            "link": f"https://scrapingsandbox.com{href}",
                            # Extrai o ID do produto a partir do link (ex: de "/product/1" pega o "1")
                            "id": href.split("/")[-1] 
                        })
    except Exception as e:
        # Se der qualquer erro (ex: internet caiu), avisa no terminal
        print(f"Erro durante o scraping: {e}")
        
    # Retorna a lista com os produtos encontrados
    return produtos_encontrados

def Buscar_detalhes_produto(id_produto):
    url_produto = f"https://scrapingsandbox.com/product/{id_produto}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        resposta = requests.get(url_produto, headers=headers, timeout=10)
        
        if resposta.status_code == 200:
            soup = BeautifulSoup(resposta.text, "html.parser")
            
            # Vamos buscar todas as tags <pre> da página.
            blocos_pre = soup.find_all("pre")
            
            for bloco in blocos_pre:
                texto = bloco.get_text()
                # Se o texto do bloco começar com '{' e tiver a palavra "id", é o nosso JSON!
                if "{" in texto and '"id"' in texto:
                    try:
                        # Tenta converter o texto em dicionário
                        dados = json.loads(texto)
                        return dados
                    except json.JSONDecodeError:
                        continue # Se falhar, tenta o próximo bloco <pre>
            
            # Se não achou na tag <pre>, tenta na tag <code>
            blocos_code = soup.find_all("code")
            for bloco in blocos_code:
                texto = bloco.get_text()
                if "{" in texto and '"id"' in texto:
                    try:
                        dados = json.loads(texto)
                        return dados
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        print(f"Erro ao buscar detalhes do produto {id_produto}: {e}")
    
    return None

app = Flask(__name__)

# Rota da página inicial
@app.route("/")
def inicio():
    return render_template("index.html")

# Rota que processa o formulário de pesquisa
@app.route("/pesquisar", methods=["POST"])
def pesquisar():
    # Pega a categoria que o usuário escolheu no formulário
    categoria = request.form.get("categoria")
    
    # Chama a função para raspar os produtos daquela categoria
    lista_de_produtos = Buscar_dados(categoria)
    
    total_produtos = len(lista_de_produtos)
    
    # Variáveis iniciais (caso não encontre nenhum produto)
    preco_medio = 0
    maior_preco = 0
    menor_preco = 0
    produto_mais_caro = "Nenhum"
    produto_mais_barato = "Nenhum"
    melhor_avaliacao = 0
    produto_melhor_avaliado = "Nenhum"

    # Só faz as contas se houver pelo menos 1 produto
    if total_produtos > 0:
        # List comprehension: Pega todos os preços, remove o "$" e converte para número (float)
        # O if no final garante que só vai converter se for um número válido (evita erros)
        precos_numericos = [float(p["preco"].replace("$", "").strip()) for p in lista_de_produtos if p["preco"].replace("$", "").strip().replace(".", "").isdigit()]
        
        # List comprehension: Pega todas as avaliações e converte para número (float)
        avaliacoes_numericas = [float(p["avaliacao"]) for p in lista_de_produtos if p["avaliacao"].replace(".", "").isdigit()]

        if precos_numericos:
            # Calcula a média de preços
            preco_medio = sum(precos_numericos) / len(precos_numericos)
            # Encontra o maior e o menor preço
            maior_preco = max(precos_numericos)
            menor_preco = min(precos_numericos)
            
            # Encontra o NOME do produto mais caro e do mais barato
            produto_mais_caro = max(lista_de_produtos, key=lambda x: float(x["preco"].replace("$", "").strip()) if x["preco"].replace("$", "").strip().replace(".", "").isdigit() else 0)["nome"]
            produto_mais_barato = min(lista_de_produtos, key=lambda x: float(x["preco"].replace("$", "").strip()) if x["preco"].replace("$", "").strip().replace(".", "").isdigit() else 999999)["nome"]

        if avaliacoes_numericas:
            # Encontra a maior nota e o nome do produto com a melhor avaliação
            melhor_avaliacao = max(avaliacoes_numericas)
            produto_melhor_avaliado = max(lista_de_produtos, key=lambda x: float(x["avaliacao"]) if x["avaliacao"].replace(".", "").isdigit() else 0)["nome"]

    # Envia todos os dados calculados para a página HTML (produtos.html)
    return render_template(
        "produtos.html", 
        produtos=lista_de_produtos, 
        categoria=categoria,
        total=total_produtos,
        media=round(preco_medio, 2),      # Arredonda para 2 casas decimais
        maior=round(maior_preco, 2),
        menor=round(menor_preco, 2),
        mais_caro=produto_mais_caro,
        mais_barato=produto_mais_barato,
        melhor_avaliacao=round(melhor_avaliacao, 2),
        melhor_avaliado=produto_melhor_avaliado
    )

# Rota para a página de detalhes do produto
# O <int:id> significa que a URL espera um número inteiro (ex: /produto/1, /produto/2)
@app.route("/produto/<int:id>")
def ver_produto(id):
    # Chama a função que vai na página do produto e extrai o JSON
    dados_produto = Buscar_detalhes_produto(id)
    
    if dados_produto:
        # Se achou os dados, renderiza a página de detalhes passando o dicionário
        return render_template("detalhes.html", produto=dados_produto)
    else:
        # Se não achou, retorna uma mensagem de erro 404 (não encontrado)
        return "Produto não encontrado", 404


if __name__ == "__main__":
    app.run(debug=True)