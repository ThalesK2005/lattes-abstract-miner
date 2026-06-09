import xml.etree.ElementTree as ET
import json
import re
import requests
import time
from bs4 import BeautifulSoup


arquivo_xml = "lattes.xml" #coloque o nome do arquivo .xml aqui :D


def consertar_texto(texto):
    if not texto: return ""
    try:
        return texto.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto

def limpar_html(texto):
    if not texto: return ""
    
    return re.sub(r'<[^>]+>', '', texto).strip()

def remontar_abstract_openalex(inverted_index):
    if not inverted_index: return ""
    palavras = {}
    for palavra, posicoes in inverted_index.items():
        for pos in posicoes:
            palavras[pos] = palavra
    abstract_remontado = " ".join([palavras[i] for i in sorted(palavras.keys())])
    return abstract_remontado

def buscar_abstract_cascata(doi_puro):
    """Tenta 4 métodos diferentes para conseguir o Resumo."""
    
    # 1. Tentativa: CROSSREF
    try:
        req1 = requests.get(f"https://api.crossref.org/works/{doi_puro}", timeout=8)
        if req1.status_code == 200:
            abs_cross = req1.json().get('message', {}).get('abstract', '')
            if abs_cross: return limpar_html(abs_cross), "Crossref (API)"
    except: pass

    # 2. Tentativa: SEMANTIC SCHOLAR
    try:
        req2 = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi_puro}?fields=abstract", timeout=8)
        if req2.status_code == 200:
            abs_sem = req2.json().get('abstract', '')
            if abs_sem: return limpar_html(abs_sem), "Semantic Scholar (API)"
    except: pass

    # 3. Tentativa: OPENALEX
    try:
        req3 = requests.get(f"https://api.openalex.org/works/doi:{doi_puro}", timeout=8)
        if req3.status_code == 200:
            index_open = req3.json().get('abstract_inverted_index', {})
            abs_open = remontar_abstract_openalex(index_open)
            if abs_open: return abs_open, "OpenAlex (API)"
    except: pass

    
    try:
        url_direta = f"https://doi.org/{doi_puro}"
        headers_navegador = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        req4 = requests.get(url_direta, headers=headers_navegador, timeout=15, allow_redirects=True)
        
        if req4.status_code == 200:
            soup = BeautifulSoup(req4.text, 'html.parser')
            
            
            meta_abstract = soup.find('meta', attrs={'name': 'citation_abstract'}) or \
                            soup.find('meta', attrs={'name': 'DC.Description'}) or \
                            soup.find('meta', attrs={'name': 'dc.description'}) or \
                            soup.find('meta', attrs={'property': 'og:description'})
            
            if meta_abstract and meta_abstract.get('content'):
                abs_scraping = meta_abstract['content']
                
                if len(abs_scraping) > 50: 
                    return limpar_html(abs_scraping), "Web Scraping Direto (Site da Revista)"
    except Exception as e:
        pass

    return "", "Nenhuma Fonte"

def gerar_json_blindado():
    caminho_xml = arquivo_xml 
    
    print("1. A ler o Currículo Lattes...")
    try:
        with open(caminho_xml, 'r', encoding='ISO-8859-1') as f:
            xml_content = f.read()
    except FileNotFoundError:
        print("Erro: Ficheiro XML não encontrado.")
        return

    xml_no_decl = re.sub(r'<\?xml[^>]+\?>', '', xml_content)
    root = ET.fromstring(xml_no_decl)
    
    pesquisador = consertar_texto(root.find('DADOS-GERAIS').get('NOME-COMPLETO', 'Desconhecido'))
    artigos = []

    print("2. A filtrar artigos recentes (2022-2025) com DOI...")
    for artigo in root.iter('ARTIGO-PUBLICADO'):
        dados_basicos = artigo.find('DADOS-BASICOS-DO-ARTIGO')
        detalhamento = artigo.find('DETALHAMENTO-DO-ARTIGO')
        
        if dados_basicos is not None:
            doi = dados_basicos.get('DOI', '').strip()
            doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
            
            ano_str = dados_basicos.get('ANO-DO-ARTIGO', '')
            
            if doi and ano_str.isdigit() and 2022 <= int(ano_str) <= 2025:
                titulo = consertar_texto(dados_basicos.get('TITULO-DO-ARTIGO', ''))
                revista = consertar_texto(detalhamento.get('TITULO-DO-PERIODICO-OU-REVISTA', '')) if detalhamento is not None else ''
                autores = [consertar_texto(a.get('NOME-COMPLETO-DO-AUTOR', '')) for a in artigo.findall('AUTORES')]
                
                artigos.append({
                    'pesquisador': pesquisador,
                    'titulo': titulo,
                    'nomes': ', '.join(autores),
                    'ano': int(ano_str),
                    'revista': revista,
                    'descricao': '', 
                    'doi': doi
                })

    print(f"-> {len(artigos)} artigos encontrados. A iniciar varredura de 4 camadas...\n")

    for idx, art in enumerate(artigos, 1):
        doi = art['doi']
        print(f"   [{idx}/{len(artigos)}] A pesquisar: {doi}")
        
        resumo, fonte = buscar_abstract_cascata(doi)
        
        if resumo:
            art['descricao'] = resumo
            print(f"      [+] Sucesso! Fonte: {fonte}")
        else:
            art['descricao'] = "Resumo indisponível. O texto encontra-se bloqueado num PDF fechado no site da revista."
            print("      [-] Resumo não disponível.")
            
        time.sleep(2) 

    caminho_saida = 'resultado.json'
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(artigos, f, indent=4, ensure_ascii=False)
        
    print(f"\n Concluído! O ficheiro JSON final está gerado e pronto.")

if __name__ == "__main__":
    gerar_json_blindado()