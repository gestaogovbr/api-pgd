# API do Programa de Gestão (PGD)

Repositório com o código-fonte da API do Programa de Gestão (PGD).

[![Docker Image Build & CI Tests](https://github.com/gestaogovbr/api-pgd/actions/workflows/docker-image.yml/badge.svg)](https://github.com/gestaogovbr/api-pgd/actions/workflows/docker-image.yml)

## Contextualização

O Programa de Gestão, segundo a
[Instrução Normativa n.º ____, de ____ 2023](),
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

## Instalando a API em ambiente de desenvolvimento

1. Instalar Docker CE [aqui!](https://docs.docker.com/get-docker/)
2. Clonar o repositório:

    ```bash
    git clone git@github.com:gestaogovbr/api-pgd.git
    ```

3. Dentro da pasta clonada execute o comando para gerar a imagem docker
   do container da API:

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

5. A gestão de usuários é realizada por uma aplicação chamada Fief.
   É necessário inicializá-la para obter as suas configurações, as quais
   serão preenchidas no passo seguinte.

   ```bash
   docker run -it --rm ghcr.io/fief-dev/fief:latest fief quickstart --docker
   ```

6. Criar um arquivo `.env` a partir do modelo:

  ```bash
  cp .env.template .env
  ```
  
  e editá-lo para preenchê-lo com as configurações necessárias referentes a:
  
  * o servidor smtp para envio de e-mails,
  * o banco de dados (Postgres), e
  * a ferramenta de gestão de usuários (Fief)

7. Tentar subir os containers:

  ```bash
  docker-compose up
  ```

  Caso apareça um erro de permissão no pgadmin, pare os containers
  (`ctrl` + `C`) e digite novamente:

  ```bash
  sudo chown -R 5050:5050 ./pgadmin_data/
  ```

  Para ajustar as permissões de arquivo em todas essas subpastas.

8. Para subir os containers:

    ```bash
    docker-compose up -d
    ```

    Estarão disponíveis os seguintes serviços:

    * http://localhost:5057 -- A API e sua interface Swagger UI em
      http://localhost:5057/docs para interagir e testar suas funcionalidades
    * http://localhost:5050 -- A interface do PGAdmin, para caso queira
      verificar os dados armazenados em ambiente de desenvolvimento
    * http://localhost:8000/admin/ -- interface do Fief para cadastro de
      usuários da API e outras configurações



### Usuário administrador

Ao realizar a configuração inicial do Fief já é criado um usuário
administrador, o qual pode alterar algumas configurações e cadastrar
novos usuários.

O usuário e senha desse usuário administrador ficam configurados nas
variáveis de ambiente `FIEF_MAIN_USER_EMAIL` e `FIEF_MAIN_USER_PASSWORD`
(vide passos 5 e 6 da configuração do ambiente).

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

    Obs.: Caso apareça uma mensagem de erro "can't stat" seguido de uma
    pasta do Pgadmin, use o comando
    `sudo chown -R usuario:usuario ./pgadmin_data/` para devolver a
    propriedade da pasta ao seu usuário antes do build do container.

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
