# API do Programa de Gestão (PGD)

Repositório com o código-fonte da API do PGD

## Rodando a API

1. Instalar Docker CE [aqui!](https://docs.docker.com/get-docker/)
2. Clonar o repositório:
> ```$ git clone http://git.planejamento.gov.br/seges-cginf/api-pgd.git```

3. Dentro da pasta clonada execute o comando para gerar a imagem docker:
> ```$ cd api-pgd```

> ```$ docker build -t api-pgd .```

O parâmetro `-t api-pgd` define uma tag(um nome) para a imagem docker gerada.
4. Para subir os containers:
> ```$ docker-compose up -d```

A API está disponível em http://localhost:5057 e em http://localhost:5057/docs você acessa a interface para interagir com a API.

## Desenvolvendo

Durante o desenvolvimento é comum a necessidade de inclusão de novas biliotecas python ou a instalação de novos pacotes linux. Para que as mudanças surtam efeitos é necessário apagar os containers e refazer a imagem docker.

1. Desligando e removendo os conteiners:
> `$ docker-compose down`

2. Buildando novamente o Dockerfile para gerar uma nova imagem:
> ```$ docker build --rm -t api-pgd .```

O parâmetro `--rm` remove a imagem criada anteriormente.
3. Agora a aplicação já pode ser subida novamente:
> ```$ docker-compose up -d```

Alternativamente você pode subir a aplicação sem o parâmetro _detached_ `-d` possibilitando visualizar o log em tempo real, muito útil durante o desenvolvimento.
> ```$ docker-compose up```

## Arquitetura da solução
O arquivo `docker-compose.yml` descreve a receita dos conteiners que compõem a solução. Atualmente são utilizados 3 containers: um rodando o BD **Postgres 11**, outro rodando a **API** e outro rodando o **PgAdmin** para acessar o Postgres e realizar consultas ou qualquer manipulação no BD.

Consulte o `docker-compose.yml` para descobrir o login e senha do PgAdmin e do Postgres. No PgAdmin utilize `'db'` como valor para o endereço do Postgres. Isso é necessário porquê o os containers utilizam uma rede interna do Docker para se comunicarem.