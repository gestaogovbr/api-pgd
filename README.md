# API do Programa de Gestão (PGD)

Repositório com o código-fonte da API do Programa de Gestão (PGD).

[![Docker Image Build & CI Tests](https://github.com/gestaogovbr/api-pgd/actions/workflows/docker-image.yml/badge.svg)](https://github.com/gestaogovbr/api-pgd/actions/workflows/docker-image.yml)

## Contextualização

O
[Programa de Gestão](https://www.gov.br/servidor/pt-br/assuntos/programa-de-gestao),
segundo a
[Instrução Normativa Conjunta SEGES-SGPRT n.º 24, de 28 de julho de 2023](https://www.in.gov.br/en/web/dou/-/instrucao-normativa-conjunta-seges-sgprt-/mgi-n-24-de-28-de-julho-de-2023-499593248),
da Secretaria de Gestão e Inovação (SEGES e da Secretaria de Gestão de
Pessoas e de Relações de Trabalho (SGPRT) do Ministério da Gestão e da
Inovação em Serviços Públicos (MGI), é um:

> programa indutor de melhoria de desempenho institucional no serviço
> público, com foco na vinculação entre o trabalho dos participantes, as
> entregas das unidades e as estratégias organizacionais.

As atividades mensuradas podem ser realizadas tanto presencialmente
quanto na modalidade de teletrabalho.

O objetivo desta API integradora é receber os dados enviados por diversos
órgãos e entidades da administração, por meio dos seus próprios sistemas
que operacionalizam o PGD no âmbito de sua organização, de modo a
possibilitar a sua consolidação em uma base de dados.

## Instalando a API em ambiente de desenvolvimento

1. Instalar Docker CE (as [instruções](https://docs.docker.com/get-docker/)
   variam conforme o sistema operacional).

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

5. A gestão de usuários é realizada por uma aplicação chamada Fief. Para
   obter as suas configurações iniciais, as quais serão preenchidas no
   passo seguinte, utilize o script:

   ```bash
   ./load_fief_env.sh
   ```

   Será pedido um endereço de e-mail e uma nova senha para o usuário
   administrador do Fief.

   O script ira criar o arquivo .env as configurações necessárias referentes a:
   
   * o servidor smtp para envio de e-mails,
   * o banco de dados (Postgres), e
   * a ferramenta de gestão de usuários (Fief), gerados no passo anterior.

6. Na gestão de usuários e controle de acesso da API é usada a aplicação
   [Fief](https://www.fief.dev/). Para o seu correto funcionamento pela
   interface Swagger UI, é necessário que ela seja alcançável pelo mesmo
   host, tanto no navegador quanto dentro do container. Para isso, em
   ambiente de desenvolvimento, será necessário estabelecer um alias
   `fief` para o host `localhost` no arquivo `/etc/hosts`. Abra-o e
   acrescente a seguinte linha:

   ```
   127.0.1.1	fief
   ```

7. Para iniciar a API, suba os containers:

   ```bash
   docker-compose up
   ```

   > ⚠️ Caso apareça um erro de permissão no pgadmin, pare os containers
   > (`ctrl` + `C`) e digite novamente:
   >
   > ```bash
   > sudo chown -R 5050:5050 ./pgadmin_data/
   > ```
   >
   > Para ajustar as permissões da pasta `pgadmin_data` e todas as suas
   > subpastas

   > ⚠️ Na primeira execução, o container do Fief vai apresentar erro
   > por causa da inexistência do database `fief` dentro do Postgres.
   > Para resolver, ainda com os contêineres rodando, execute:
   >
   > ```bash
   > docker exec -it -u postgres api-pgd-db-api-pgd-1 createdb fief
   > ```

   Estarão disponíveis os seguintes serviços:

   * http://localhost:5057 -- A API e sua interface Swagger UI em
     http://localhost:5057/docs para interagir e testar suas funcionalidades
   * http://localhost:5050 -- A interface do PGAdmin, para caso queira
     verificar os dados armazenados em ambiente de desenvolvimento
   * http://fief:8000/admin/ -- interface do Fief para cadastro de
     usuários da API e outras configurações



### Usuário administrador e cadastro de usuários

Ao realizar a configuração inicial do Fief já é criado um usuário
administrador, o qual pode alterar algumas configurações e cadastrar
novos usuários.

O usuário e senha desse usuário administrador ficam configurados nas
variáveis de ambiente `FIEF_MAIN_USER_EMAIL` e `FIEF_MAIN_USER_PASSWORD`
(vide passos 5 e 6 da configuração do ambiente).

### Ajustando os containers

Durante o desenvolvimento é comum a necessidade de inclusão de novas
bibliotecas python ou a instalação de novos pacotes Linux. Para que as
mudanças surtam efeitos é necessário apagar os containers e refazer a
imagem docker.

1. Desligando e removendo os contêineres:

    ```bash
    docker-compose down
    ```

2. Construindo novamente o Dockerfile para gerar uma nova imagem:

    ```bash
    docker build --rm -t api-pgd .
    ```

    O parâmetro `--rm` remove a imagem criada anteriormente.

    > ⚠️ Obs.: Caso apareça uma mensagem de erro "can't stat" seguido de
    > uma pasta do Pgadmin, use o comando
    > `sudo chown -R usuario:usuario ./pgadmin_data/` para devolver a
    > propriedade da pasta ao seu usuário antes do build do container.

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

O arquivo `docker-compose.yml` descreve a receita dos contêineres que
compõem a solução. Atualmente são utilizados 4 containers:

* um rodando o sistema gerenciador de banco de dados **Postgres 11**,
* outro rodando a **API**,
* outro rodando o sistema de gestão de usuários e controle de acesso
  **Fief**, e
* outro rodando o **PgAdmin** para acessar o Postgres e realizar
  consultas ou qualquer manipulação no BD. O PgAdmin é útil para o
  ambiente de desenvolvimento e testes, não sendo necessário ou
  aconselhável a sua utilização em ambiente de produção. Quando utilizado
  o PgAdmin, ele estará rodando em http://localhost:5050.


## Dicas

* Consulte o `docker-compose.yml` para descobrir o login e senha do
  PgAdmin.
* O login e senha do Fief são definidos no item 5 do
  passo a passo em
  "[Instalando a API em ambiente de desenvolvimento](#instalando-a-api-em-ambiente-de-desenvolvimento)".
  Depois disso eles ficam no arquivo `.env`, bem como o `client_id` e
  o `client_secret` usados na autenticação da API (variáveis
  `FIEF_CLIENT_ID` e `FIEF_CLIENT_SECRET`, respectivamente).
* O login, senha e nome do banco do Postgres estão em variáveis de
  ambiente. A forma mais prática de fazer isto em ambiente de
  desenvolvimento é criando-se um arquivo `.env`, conforme o item 6 do
  passo a passo em
  "[Instalando a API em ambiente de desenvolvimento](#instalando-a-api-em-ambiente-de-desenvolvimento)".
* No PgAdmin utilize `'db-api-pgd'` como valor para o endereço do
  Postgres. Isso é necessário porquê os contêineres utilizam uma rede
  interna do Docker para se comunicarem.
* Caso a modelagem ORM seja alterada, pode ser mais simples remover
  (dropar) o BD e recriá-lo novamente apenas subindo a solução. Para
  remover o BD utilize o PgAdmin.
* Para fazer *deploy* usando algum outro banco de dados externo, basta
  redefinir a variável de ambiente `SQLALCHEMY_DATABASE_URL` no
  contêiner da aplicação.

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
