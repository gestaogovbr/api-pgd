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

Explore a seção **Schemas** abaixo nesta documentação para ler as
descrições dos campos e saber quais são obrigatórios.

-------


## Endpoints

A API consiste em um endpoint de autenticação do usuário da API e três
endpoints de domínio.

Como algumas entidades fazem referência a outras, as que são referenciadas
precisam ser enviadas primeiro. Por isso, os dados devem ser enviados
na seguinte ordem:

1. Participantes
2. Planos de Entrega
3. Planos de Trabalho

![Diagrama do Modelo de Dados da API PGD 3](https://raw.githubusercontent.com/gestaogovbr/api-pgd/main/docs/images/api-pgd-3-diagrama.svg)


### 0. Auth

Os **Usuários** podem criar, editar e deletar novos usuários ou apenas
consultar dados de Participantes, Planos de Entrega e Planos de Trabalho
conforme a unidade organizacional que pertence.

Campos utilizados:

* `email`: Em formato nome@dominio.com;
* `password`;
* `is_admin`: Se pode criar, editar e deletar usuários ou, ainda, ter
  acesso a todas as unidades da API;
* `disabled`: Se está desativado. Se for verdadeiro não poderá se autenticar
  na API;
* `origem_unidade`: O nome do sistema de unidades utilizado nos campos que
  se referem a unidades (SIAPE ou SIORG);
* `cod_unidade_autorizadora`: Unidade autorizadora do PGD à qual o usuário
  pertence e está autorizado a enviar e consultar dados.


### 0.1. Permissões

Em todos os endpoints são utilizados os campos `orgiem_unidade` e
`cod_unidade_autorizadora` para delimitar o escopo de permissões para o
usuário enviar e consultar dados.

O `cod_unidade_autorizadora` é o código da unidade organizacional (UORG) no
Sistema Integrado de Administração de Recursos Humanos (SIAPE)
corresponde à Unidade de autorização. Referente ao artigo 3º do Decreto
nº 11.072, de 17 de maio de 2022. De forma geral, são os "Ministros de
Estado, os dirigentes máximos dos órgãos diretamente subordinados ao
Presidente da República e as autoridades máximas das entidades". Em
termos de SIAPE, geralmente é o código Uorg Lv1. O próprio Decreto,
contudo, indica que tal autoridade poderá ser delegada a dois níveis
hierárquicos imediatamente inferiores, ou seja, para Uorg Lv2 e Uorg Lv3.
Haverá situações, portanto, em que uma unidade do Uorg Lv1 de nível 2 ou
3 poderá enviar dados diretamente para API.

Exemplo: "Ministério da Gestão e da Inovação em Serviços Públicos" ou
"Conselho de Controle de Atividades Financeiras"

Obs: A instituição que não esteja no SIAPE pode usar o código SIORG.
Nesse caso, utilizar o valor "SIORG" no campo `origem_unidade`.


### 1. Participantes

* O `cpf` deve possuir exatamente 11 dígitos e sem máscaras.
* A `matricula_siape` deve possuir 7 dígitos.
* Valores permitidos para a `situacao` do agente público no Programa de
  Gestão e Desempenho (PGD):
  * `0`: Inativo;
  * `1`: Ativo.
* Valores permitidos para a `modalidade_execucao`:
  * `1`: Presencial;
  * `2`: Teletrabalho Parcial;
  * `3`: Teletrabalho Integral;
  * `4`: Teletrabalho com Residência no Exterior.
* A `data_assinatura_tcr` não pode ser data futura.

**Atenção:** os Participantes devem ser enviados antes dos Planos de
Trabalho.


### 2. Planos de Entregas

Os **Planos de Entregas** representam as entregas previstas para aquela
unidade no âmbito do Programa de Gestão. Eles devem seguir as seguintes
regras:

* A `data_termino` e a `data_avaliacao`, quando presente, devem ser iguais
  ou posteriores à `data_inicio`.
* Um Plano de Entregas não pode abranger período maior que 1 ano.
* Não deve haver sobreposição de intervalos (`data_inicio` e
  `data_termino`) entre diferentes Planos de Entrega na mesma unidade
  (`cod_unidade_executora`).
* Para o campo `status` são permitidos os seguintes valores:
  * `1`: Cancelado;
  * `2`: Aprovado;
  * `3`: Em execução;
  * `4`: Concluído;
  * `5`: Avaliado.
* O `status` `5` (Avaliado) só poderá ser usado se os campos `avaliacao` e
  `data_avaliacao` estiverem preenchidos.
* O campo `avaliacao` admite valores de `1` a `5`.

**Atenção:** os Planos de Entrega devem ser enviados antes dos Planos de
Trabalho.


#### 2.1. Entrega

* Os valores `id_entregas` devem ser únicos dentro do mesmo Plano de Entregas.
* O campo `meta_entrega` tem que ser um inteiro maior ou igual a zero.
* Para o campo `tipo_meta` são permitidos os seguintes valores:
  * `unidade`
  * `percentual` (nesse caso, `meta_entrega` tem que estar entre `0` e `100`)


### 3. Planos de Trabalho

Os **Planos de Trabalho** submetidos devem seguir as seguintes regras:
* A `data_termino` do Plano de Trabalho deve ser igual ou posterior à
  `data_inicio`.
* Um Plano de Trabalho não pode abranger período maior que 1 ano.
* Não deve haver sobreposição de intervalos (`data_inicio` e
  `data_termino`) entre diferentes Planos de Trabalho na mesma
  unidade (`cod_unidade_executora`) e mesmo participante.
* O `cpf_participante` deve se referir a um participante já cadastrado
  pelo endpoint **Participante**.
* O valor de `carga_horaria_disponivel` deve ser maior ou igual a zero.


#### 3.1. Contribuição

* Valores permitidos para a `tipo_contribuicao`:
  * `1`: Contribuição para entrega da própria unidade de execução do
    participante;
    * Nesse caso, os campos `id_plano_entregas` e `id_entrega` ficam sendo
      obrigatórios;
  * `2`: Contribuição não vinculada diretamente a entrega, mas necessária
    ao adequado funcionamento administrativo (por exemplo, Atividades de
    apoio, assessoramento e desenvolvimento, e Atividades de gestão de
    equipes e entregas);
    * Nesse caso, os campos `id_plano_entregas` e `id_entrega` não podem
      conter valores;
  * `3`: Contribuição vinculada a entrega de outra unidade de execução,
    inclusive de outros órgãos e entidades.
* O valor do campo `percentual_contribuicao` tem que estar entre `0` e `100`.


#### 3.2. Avaliação de Registro de Execução

* A `data_inicio_periodo_avaliativo` deve ser igual ou posterior à
  `data_inicio` do Plano de Trabalho.
* A `data_fim_periodo_avaliativo` precisa ser igual ou posterior à
  `data_inicio_periodo_avaliativo`.
* Não pode haver sobreposições entre os períodos definidos por
  `data_inicio_periodo_avaliativo` e `data_fim_periodo_avaliativo`,
  entre diferentes Avaliações de Registro de Execução para um mesmo
  Plano de Trabalho.
* O campo `avaliacao_registros_execucao` admite valores de `1` a `5`.


-------

Para comunicar erros na aplicação e interagir com a equipe de
desenvolvimento
[acesse aqui](https://github.com/gestaogovbr/api-pgd/issues).
