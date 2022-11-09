# API do Programa de Gestão (PGD)

Repositório com o código-fonte da API do Programa de Gestão (PGD).

[![Docker Image Build & CI Tests](https://github.com/economiagovbr/api-pgd/actions/workflows/docker-image.yml/badge.svg)](https://github.com/economiagovbr/api-pgd/actions/workflows/docker-image.yml)

## Contextualização

O Programa de Gestão, segundo a
[Instrução Normativa n.º 65, de 30 de julho de 2020](https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-65-de-30-de-julho-de-2020-269669395),
da Secretaria de Gestão e Desempenho de Pessoal (SGP) do Ministério da
Economia, é uma:

> ferramenta de gestão autorizada em ato normativo de Ministro de Estado
> e respaldada pela norma de procedimentos gerais, que disciplina o
> exercício de atividades em que os resultados possam ser efetivamente
> mensurados, cuja execução possa ser realizada pelos participantes.

As atividades mensuradas podem ser realizadas tanto presencialmente
quanto na modalidade de teletrabalho.

O objetivo desta API integradora é receber os dados enviados por
diversos órgãos da administração, de modo a possibilitar a sua
consolidação em uma base de dados.

## Rodando a API

1. Instalar Docker CE [aqui!](https://docs.docker.com/get-docker/)
2. Clonar o repositório:

    ```bash
    git clone git@github.com:economiagovbr/api-pgd.git
    ```

3. Dentro da pasta clonada execute o comando para gerar a imagem docker:

    ```bash
    cd api-pgd
    docker build -t api-pgd .
    ```

    O parâmetro `-t api-pgd` define uma tag (um nome) para a imagem docker
    gerada.

4. Criar diretório com permissão correta para persistência do PgAdmin:

    ```bash
    sudo mkdir -p pgadmin_data && sudo chown -R 5050:5050 ./pgadmin_data/
    ```

5. Criar um arquivo `.env` contendo o nome de usuário, senha e nome do
   banco a serem utilizados pelo Postgres, e configuração do servidor
   smtp:

    ```bash
    echo "POSTGRES_USER=postgres
    POSTGRES_PASSWORD=postgres
    POSTGRES_DB=api_pgd
    MAIL_USERNAME=api-pgd@email.com.br
    MAIL_FROM=api-pgd@email.com.br
    MAIL_PORT=25
    MAIL_SERVER=smtp.email.com.br
    MAIL_FROM_NAME="API PGD"
    MAIL_PASSWORD=PASSWORD" > .env
    ```

6. Tentar subir os containers:

    ```bash
    docker-compose up
    ```

    Vai dar um erro de permissão no pgadmin. Quando a mensagem de erro
    aparecer, pare os containers (`ctrl` + `C`) e digite novamente:

    ```bash
    sudo chown -R 5050:5050 ./pgadmin_data/
    ```

    Para ajustar as permissões de arquivo em todas as novas subpastas.

6. Para subir os containers:

    ```bash
    docker-compose up -d
    ```

    A API está disponível em http://localhost:5057 e em
    http://localhost:5057/docs você acessa a interface para interagir com a
    API.

### Criando o usuário administrador

Para começar a usar a API, é necessário primeiro criar um superusuário,
que será o administrador do sistema. Para maior segurança, esse
superusuário só pode ser criado a partir da linha de comando dentro do
container da API. Para isso, acesse o terminal do container:

```bash
docker exec -it api-pgd_web_1 /bin/bash
```

A partir do shell da aplicação, digite:

```bash
./admin_tool.py --create_superuser
```

e a ferramenta de administração irá solicitar o e-mail, senha e código
da unidade para o superusuário.

Os demais usuários poderão ser criados a partir da interface Swagger ou
por chamada à API, autenticando-se como o superusuário administrador e
utilizando o método `/auth/register`.

## Desenvolvendo

Durante o desenvolvimento é comum a necessidade de inclusão de novas
bibliotecas python ou a instalação de novos pacotes linux. Para que as
mudanças surtam efeitos é necessário apagar os containers e refazer a
imagem docker.

1. Desligando e removendo os contêineres:

    ```bash
    docker-compose down
    ```

2. Buildando novamente o Dockerfile para gerar uma nova imagem:

    ```bash
    docker build --rm -t api-pgd .
    ```

    O parâmetro `--rm` remove a imagem criada anteriormente.

3. Agora a aplicação já pode ser subida novamente:

    ```bash
    docker-compose up -d
    ```

    Alternativamente você pode subir a aplicação sem o parâmetro _detached_
    `-d` possibilitando visualizar o log em tempo real, muito útil durante o
    desenvolvimento.

    ```bash
    docker-compose up
    ```

## Arquitetura da solução
O arquivo `docker-compose.yml` descreve a receita dos conteiners que
compõem a solução. Atualmente são utilizados 3 containers: um rodando o
BD **Postgres 11**, outro rodando a **API** e outro rodando o
**PgAdmin** para acessar o Postgres e realizar consultas ou qualquer
manipulação no BD. O PgAdmin é útil para o ambiente de desenvolvimento
e testes, não sendo necessário ou aconselhável a sua utilização em
ambiente de produção. Quando utilizado o PgAdmin, ele estará rodando em
http://localhost:5050.


## Dicas

* Consulte o `docker-compose.yml` para descobrir o login e senha do
  PgAdmin
* O login, senha e nome do banco do Postgres estão em variáveis de
  ambiente. A forma mais prática de fazer isto em ambiente de
  desenvolvimento é criando-se um arquivo `.env`, conforme o item 5 do
  passo a passo em "[Rodando a API](#rodando-a-api)"
* No PgAdmin utilize `'db'` como valor para o endereço do Postgres. Isso
  é necessário porquê os contêineres utilizam uma rede interna do Docker
  para se comunicarem
* Caso a modelagem ORM seja alterada, pode ser mais simples remover
  (dropar) o BD e recriá-lo novamente apenas subindo a solução. Para
  remover o BD utilize o PgAdmin
* Para fazer *deploy* usando algum outro banco de dados externo, basta
  redefinir a variável de ambiente `SQLALCHEMY_DATABASE_URL` no
  contêiner da aplicação

## Rodando testes
É necessário entrar no container para rodar os testes:

```bash
docker exec -it api-pgd_web_1 /bin/bash
```

Para rodar os testes execute:

```bash
pytest tests/
```

Para rodar no modo verboso útil para debugar:

```bash
pytest tests/ -vv
```

Para rodar uma bateria de testes específica, especifique o arquivo que
contém os testes desejados. Por exemplo, os testes sobre atividades:

```bash
pytest tests/atividade_test.py
```

Para rodar um teste específico utilize o parâmetro `-k`. Este exemplo
roda apenas o teste `test_create_pt_invalid_cpf`:

```bash
pytest tests/ -k test_create_pt_invalid_cpf -vv
```
