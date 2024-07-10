API integradora de dados de sistemas do Programa de Gestão, usado para
o teletrabalho na administração pública federal.

[![Docker Image Build & CI Tests](https://github.com/gestaogovbr/api-pgd/actions/workflows/ci_tests.yml/badge.svg)](https://github.com/gestaogovbr/api-pgd/actions/workflows/ci_tests.yml)


## TL;DR (too long; didn't read)

Para iniciar e configurar os serviços com configurações default e já começar
a desenvolver:

```bash
git clone git@github.com:gestaogovbr/api-pgd.git && \
cd api-pgd && \
make up
```

> Exemplos de uso da api em [docs/examples/](docs/examples/)

---


## Índice

(para começar a desenvolver)
* [1. Contextualização](#1-contextualização)
* [2. Init, up and down dos serviços em dev](#2-init-up-and-down-dos-serviços-em-dev)
* [3. Rodando testes](#3-rodando-testes)
---
(informações extras)
* [4. Informações e Configurações adicionais](#4-informações-e-configurações-adicionais)
* [5. Arquitetura da solução](#5-arquitetura-da-solução)
* [6. Preparando um novo release](#6-preparando-um-novo-release)
* [7. Dicas](#7-dicas)

---


## 1. Contextualização

O [Programa de Gestão](https://www.gov.br/servidor/pt-br/assuntos/programa-de-gestao),
segundo a
[Instrução Normativa Conjunta SEGES-SGPRT n.º 24, de 28 de julho de 2023](https://www.in.gov.br/en/web/dou/-/instrucao-normativa-conjunta-seges-sgprt-/mgi-n-24-de-28-de-julho-de-2023-499593248),
da Secretaria de Gestão e Inovação (SEGES e da Secretaria de Gestão de
Pessoas e de Relações de Trabalho (SGPRT) do
[Ministério da Gestão e da Inovação em Serviços Públicos (MGI)](https://www.gov.br/gestao/pt-br), é um:

> programa indutor de melhoria de desempenho institucional no serviço
> público, com foco na vinculação entre o trabalho dos participantes, as
> entregas das unidades e as estratégias organizacionais.

As atividades mensuradas podem ser realizadas tanto presencialmente
quanto na modalidade de teletrabalho.

O objetivo desta API integradora é receber os dados enviados por diversos
órgãos e entidades da administração, por meio dos seus próprios sistemas
que operacionalizam o PGD no âmbito de sua organização, de modo a
possibilitar a sua consolidação em uma base de dados.


## 2. Init, up and down dos serviços em dev


### 2.1. Instalar Docker CE

Instruções em [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
variam conforme o sistema operacional.


### 2.2. Clonar o repositório

```bash
git clone git@github.com:gestaogovbr/api-pgd.git
```

### 2.3. Variáveis de ambiente

São definidas no [docker-compose.yml](docker-compose.yml):
  * [db](docker-compose.yml#L11):
    - `POSTGRES_USER`
    - `POSTGRES_PASSWORD`
    - `POSTGRES_DB`
  * [api-pgd](docker-compose.yml#L31):
    - `SQLALCHEMY_DATABASE_URL`
    - `SECRET`
    - `ACCESS_TOKEN_EXPIRE_MINUTES`
    - `API_PGD_ADMIN_USER`
    - `API_PGD_ADMIN_PASSWORD`


### 2.4. Iniciando os serviços (`banco` e `api-pgd`)

```bash
make up
```

> ⚠️  Caso apareçam erros de permissão em `./mnt/pgdata`, pare os containers
> (`ctrl` + `C`) e digite:
>
> ```bash
> sudo chown -R 999 ./mnt/pgdata/
> ```
>
> Para ajustar as permissões das pastas `./mnt/pgdata/` e todas as suas
> subpastas


### 2.5. Conferir Acessos

  * [`http://localhost:5057/docs`](http://localhost:5057/docs): swagger ui da api-pgd
  * [`http://localhost:5057`](http://localhost:5057): endpoint da api-pgd


### 2.6. Desligar serviços

  ```bash
  make down
  ```


## 3. Rodando testes


### 3.1. Todos
```bash
make tests
```

### 3.2. Selecionado

Para rodar uma bateria de testes específica, especifique o arquivo que
contém os testes desejados. Por exemplo, os testes sobre atividades:

```bash
make test TEST_FILTER=test_create_huge_plano_trabalho
```

---
---


## 4. Informações e Configurações adicionais

>  **[ATENÇÃO]:** Se você chegou até aqui seu ambiente está funcionando e pronto
> para desenvolvimento.
>  As sessões a seguir são instruções para edição de algumas configurações do ambiente.


### 4.1. Atualizando imagem do api-pgd

Durante o desenvolvimento é comum a necessidade de inclusão de novas
bibliotecas `python` ou a instalação de novos pacotes `Linux`. Para que
as mudanças surtam efeitos é necessário apagar os containers e refazer a
imagem docker.

```bash
make build
```

> O [docker-compose](docker-compose.yml) está configurado para sempre fazer
> pull da imagem no `ghcr`. Caso você edite o `Dockerfile`, para conferir
> as alterações no ambiente local, comente a linha
> [pull_policy: always](docker-compose.yml#L23).

Para subir os serviços novamente:

```bash
make up
```

> Caso deseje subir os serviços com os logs na mesma sessão do terminal:
> usar o comando `$ docker compose up --wait` em vez de `$ make up`


## 5. Arquitetura da solução

O arquivo [docker-compose.yml](docker-compose.yml) descreve a `receita`
dos contêineres que compõem a solução. Atualmente são utilizados `2 containers`:

* [db](docker-compose.yml#L4); [postgres:16](https://hub.docker.com/_/postgres)
* [api-pgd](docker-compose.yml#L21); [ghcr.io/gestaogovbr/api-pgd:latest](Dockerfile)


## 6. Preparando um novo *release*

Para preparar um novo *release*, primeiro atualize o arquivo
[release-notes.md](release-notes.md) com todas as modificações feitas
desde o último *release*. Para saber o que mudou, veja lista de *pull
requests* que foram mesclados e os commits realizados no período.

Determine qual será o número da versão, utilizando a lógica da *semantic
versioning* ({major}.{minor}.{release}):

* para correções de bugs, mudanças na documentação e outras modificações
  que não alterem a interface da API (isto é, clientes programados para a
  versões anteriores continuarão a funcionar), incremente o
  ***release***;
* para alterações que modifiquem a interface da API e que podem
  necessitar de adaptações nos clientes existentes, incremente o
  ***minor***;
* para grandes alterações que modifiquem fundalmentalmente o modelo de
  dados, baseados em uma base legal diferente ou um modelo de gestão
  diferente, incremente o ***major***.

Certifique-se de que todos os testes estão passando.

Para realizar deploy em ambiente de homologação, simplesmente crie uma
tag no git com o número da versão, separado por pontos, sem "v" ou
nenhuma outra informação adicional (ex.: `2.0.0`).


## 7. Dicas

* Exemplos de uso da api em [docs/examples/](docs/examples/)
* Para depuração, caso necessite ver como está o banco de dados no ambiente
  local, altere a porta do Postgres no [docker-compose.yml](docker-compose.yml#L8)
  de `"5432"` para `"5432:5432"` e o banco ficará exposto no host via `localhost`.
  Depois, basta usar uma ferramenta como o [dbeaver](https://dbeaver.io/)
  para acessar o banco.
* Para subir o ambiente usando algum outro banco de dados externo, basta
  redefinir a variável de ambiente `SQLALCHEMY_DATABASE_URL` no
  [docker-compose.yml](docker-compose.yml#L37).
