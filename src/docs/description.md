Esta API possibilita que órgãos federais enviem  para a SEGES/MGI os
Planos de Entregas e os Planos de Trabalho da sua força de trabalho que
participa do
[Programa de Gestão](https://www.gov.br/servidor/pt-br/assuntos/programa-de-gestao).
Para solicitar credenciais para submissão de dados, entre em contato com
[pgd@economia.gov.br](mailto:pgd@economia.gov.br)

### Fundamentação legal

> #### Instrução Normativa Conjunta SEGES-SGPRT n.º 24, de 28 de julho de 2023
>
> Estabelece orientações a serem observadas pelos órgãos e entidades
> integrantes do Sistema de Pessoal Civil da Administração Federal -
> Sipec e do Sistema de Organização e Inovação Institucional do Governo
> Federal - Siorg, relativas à implementação e execução do Programa de
> Gestão e Desempenho - PGD.
>
> Art. 29. Os órgãos e entidades enviarão ao órgão central do Siorg, via
> Interface de Programação de Aplicação- API, os dados sobre a execução
> do PGD, observadas a documentação técnica e a periodicidade a serem
> definidas pelo Comitê de que trata o art. 31 desta Instrução Normativa
> Conjunta.

### Esquemas de dados

Explore a seção **Schemas** abaixo nesta documentação para descobrir mais
detalhes e quais campos são obrigatórios para as Atividades e os Planos
de Trabalho.

-------

## Endpoints

A API consiste em um endpoint de autenticação do usuário da API e três
endpoints de domínio.

Como algumas entidades fazem referência a outras, as que são referenciadas
precisam ser enviadas primeiro. Por isso, os dados devem ser enviados
na seguinte ordem:

1. Auth
2. Participantes
3. Planos de Entrega
4. Planos de Trabalho

### 1. Auth

Os **Usuários** podem criar, editar e deletar novos usuários ou apenas
consultar dados de Participantes, Planos de Entrega e Planos de Trabalho
conforme a unidade organizacional que pertence.

Campos utilizados:

* `username/email`: Em formato foo@oi.com;
* `password`;
* `is_admin`: Se pode criar, editar e deletar usuários;
* `disabled`: Se está ativo. Se pode consultar dados na api;
* `cod_SIAPE_instituidora`: Unidade que pertence.

### 2. Participantes

* O `cpf_participante` deve possuir exatamente 11 dígitos e sem máscaras.
* A `matricula_siape` deve possuir 7 dígitos.
* `jornada_trabalho_semanal` deve ser maior que 0.
* Valores permitidos para a `modalidade_execucao`:
  * `1`: Presencial;
  * `2`: Teletrabalho Parcial;
  * `3`: Teletrabalho Integral;
  * `4`: Teletrabalho com Residência no Exterior.


### 3. Planos de Entregas

Os **Planos de Entregas** representam as entregas previstas para aquela
unidade no âmbito do Programa de Gestão. Eles devem seguir as seguintes
regras:

* Não deve haver sobreposição de intervalos (`data_inicio_plano_entregas`
  e `data_termino_plano_entregas`) entre diferentes Planos de Entrega na
  mesma unidade (`cod_SIAPE_unidade_plano`).

**Atenção:** os Planos de Entrega devem ser enviados antes dos Planos de
Trabalho.

#### 3.1. Entrega

* Para o campo `tipo_meta` são permitidos os seguintes valores:
  * `1`: absoluto
  * `2`: percentual

### 3.2. Planos de Trabalho

Os **Planos de Trabalho** submetidos devem seguir as seguintes regras:
* O `id_plano_entrega_unidade` deve ser único para cada Plano de Trabalho.
* Ao utilizar o método PUT do Plano de Trabalho, o
  `id_plano_entrega_unidade` que compõe a URL deve ser igual ao fornecido
  no JSON.
* A `data_inicio_plano` do Plano de Trabalho deve ser menor ou igual à
  `data_termino_plano`.
* O `cpf_participante` deve se referir a um participante já cadastrado
  pelo endpoint **Participante**.
* Não deve haver sobreposição de intervalos (`data_inicio_plano` e
  `data_termino_plano`) entre diferentes Planos de Entrega na mesma
  unidade (`cod_SIAPE_unidade_plano`) e mesmo participante.

#### 3.2.1. Contribuição

* Valores permitidos para a `tipo_contribuicao`:
  * `1`: Contribuição para entrega da própria unidade de execução do
    participante;
  * `2`: Contribuição não vinculada diretamente a entrega, mas necessária
    ao adequado funcionamento administrativo (por exemplo, Atividades de
    apoio, assessoramento e desenvolvimento, e Atividades de gestão de
    equipes e entregas);
  * `3`: Contribuição vinculada a entrega de outra unidade de execução,
    inclusive de outros órgãos e entidades.


#### 3.2.2. Consolidação

* A `data_inicio_registro` da consolidação deve ser maior ou igual que a
  `data_inicio_plano` do Plano de Trabalho.


-------

Para comunicar erros na aplicação e interagir com a equipe de
desenvolvimento
[acesse aqui](https://github.com/gestaogovbr/api-pgd/issues).
