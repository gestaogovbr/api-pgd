# Gestão de usuários

Para realizar a gestão de usuários da API, é necessário possuir uma conta
com perfil de administrador e estar autenticado.


## Usuários

Os usuários da API são contas pelas quais é possível se autentica na API
para ler ou enviar dados referentes aos sistemas do Programa de Gestão -
PGD.

Não devem ser confundidos com os usuários dos sistemas PGD, que no escopo
desta API são apenas os participantes do programa em suas respectivas
instituições e não usam diretamente esta API.

Há dois perfis de usuários:

1. **Administrador.** Pode cadastrar e alterar o cadastro de um usuário
   comum.
2. **Usuário comum.** Gestor setorial de dados de um sistema no âmbito do
   PGD. Pode ler e escrever dados referentes somente à sua própria
   organização (`cod_unidade_autorizadora`).


## Listar os usuários cadastrados

Para listar todos os usuários cadastrados, use o endpoint `GET /users`.
Não há parâmetros. Será mostrado o e-mail, o perfil, a informação se a
conta está ou não ativa e o código SIAPE da sua instituição.


## Cadastrar um novo usuário

Obtenha primeiro o código SIAPE da instituição que irá integrar seus
dados do PGD por meio da API. Este código será usado no campo
`cod_unidade_autorizadora`.

Após se autenticar na API com um perfil de administrador, use o endpoint
`PUT /user/{email}`, substituindo o campo `email` como o e-mail do
usuário e preenchendo as demais informações no corpo do documento JSON,
conforme indicado na documentação Swagger.


## Alterar o cadastro de um usuário

O procedimento para alteração é o mesmo para o cadastro de um novo usuário.
Basta enviar novamente uma requisição para o endpoint `PUT /user/{email}`,
enviando no corpo do documento JSON as novas informações.

Por exemplo, para desativar ou reativar um usuário, basta preencher
o campo `disabled` com o valor `true` ou `false`, respectivamente.


## Recuperar a senha

Caso tenha esquecido sua senha, o próprio usuário pode recuperá-la usando
o endpoint `POST /user/forgot_password/{email}`. Será enviada
para o e-mail informado no seu cadastro uma mensagem contendo um token
de acesso.

Para redefinir a senha, envie `GET /user/reset_password`, passando como
parâmetros o token de acesso recebido e a nova senha desejada.
