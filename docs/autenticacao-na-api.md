# Autenticação na API

Para se autenticar na API, primeiro acesse o endereço da interface
Swagger.

> **Qual é o endereço da interface Swagger?**
>
> O endereço varia conforme o ambiente em que foi instalado.
>
> Se a API foi instalada em ambiente de desenvolvimento local, no próprio
> computador, e foram seguidas as instruções do README, o endereço será
>
> http://localhost:5057/docs/
>
> Por outro lado, se estiver tentando usar um sistema implantado em uma
> organização e você não sabe o endereço, pergunte ao administrador do
> sistema.

## Login

A autenticação na API é feita por meio do protocolo OAuth 2.0.

Para começar, clique no botão "Authorize 🔓".

![Imagem do botão "Authorize".](images/authorize-button.png)

A próxima tela "Available authorizatins" preencha os campos `username` ([API_PGD_ADMIN_USER](../docker-compose.yml#L35))
e `password` ([API_PGD_ADMIN_PASSWORD](../docker-compose.yml#L36)) conforme definidos no [docker-compose.yml](../docker-compose.yml).

Após realizado o login com sucesso, a tela "Available authorizations" irá
mostrar que já está logado. Em vez do botão "Authorize", estará visível o
botão "Logout".

![Imagem da tela "Available authorizations" com o login já realizado.](images/available-authorizations-logged-in.png)

Clique em "Close" para fechar a janela. Agora o usuário está logado.
Caso deseje realizar operações manuais na API, poderá utilizar a
interface do Swagger e preencher os formulários.

## Acesso automatizado de modo autenticado

Siga exemplos em [../examples/](../examples/).