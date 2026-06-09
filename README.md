# Lattes Abstract Miner

Um script em Python desenvolvido para extrair publicacoes recentes de um curriculo Lattes (formato XML) e buscar automaticamente os resumos (abstracts) de cada artigo utilizando o codigo DOI.

O grande diferencial deste projeto e a sua arquitetura de busca em cascata (fallback), que garante uma alta taxa de sucesso na obtencao dos textos, consultando multiplas bases de dados academicas globais e recorrendo a web scraping como ultima alternativa.

## Funcionalidades

* Leitura e parseamento de arquivos XML gerados pela plataforma Lattes.
* Filtragem automatica de artigos publicados em um intervalo de anos especifico (configurado para 2022-2025).
* Limpeza e padronizacao de caracteres corrompidos (Mojibake) exportados pelo Lattes.
* Sistema de busca de resumos em 4 camadas de contingencia.
* Exportacao dos metadados consolidados em um arquivo JSON formatado e pronto para consumo por aplicacoes web ou paineis de visualizacao.

## Arquitetura de Busca em Cascata

Para garantir que o resumo seja encontrado, o script realiza requisicoes sequenciais nas seguintes fontes:

1. **Crossref API:** Base oficial de registro mundial de DOIs.
2. **Semantic Scholar API:** Base de dados baseada em IA que mapeia e le PDFs de artigos academicos na web.
3. **OpenAlex API:** Catalogo de codigo aberto de dados bibliograficos (o script remonta os abstracts que sao devolvidos em formato de indice invertido).
4. **Web Scraping Direto (BeautifulSoup):** Se todas as APIs falharem, o script acessa a URL de resolucao do DOI, segue os redirecionamentos ate o site oficial da revista e extrai o conteudo das meta tags HTML (`citation_abstract`, `dc.description`, etc).

## Pre-requisitos

Certifique-se de ter o Python 3.x instalado em sua maquina. O projeto depende das seguintes bibliotecas externas:

* `requests`
* `beautifulsoup4`

Para instalar as dependencias, execute o comando abaixo no seu terminal:

```bash
pip install requests beautifulsoup4
