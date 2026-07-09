Esta API possibilita que órgãos federais enviem  para a SEGES/MGI os
Planos de Entregas e os Planos de Trabalho da sua força de trabalho que
participa do
[Programa de Gestão](https://www.gov.br/servidor/pt-br/assuntos/programa-de-gestao).

Esta documentação está disponível em duas formatações distintas, mas com
o mesmo conteúdo:

* [Swagger UI](/docs)
* [Redoc](/redoc)


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


### Identificação do sistema gerador

O sistema de informações que opera o Programa de Gestão no órgão, bem
como a sua versão, devem ser informados de duas maneiras:

1. No cadastro do usuário da API, no campo `sistema_gerador`, informar
   nome e versão. Ver seção "**0. Auth**", abaixo.
2. No cabeçalho `User-Agent` da requisição feita pelo sistema ao acessar
   a API, informar sequência de texto (string) padronizada, contendo:
   - nome do sistema
   - versão do sistema
   - url onde se pode obter uma descrição ou informações gerais sobre o
     sistema.

   A string deve seguir o formato: `Nome do sistema/versão (+url)`.
   Exemplo:

   `User-Agent: Petrvs/2.1 (https://www.gov.br/servidor/pt-br/assuntos/programa-de-gestao/sistemas-e-api-de-dados/sistema-pgd-petrvs)`.


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
  pertence e está autorizado a enviar e consultar dados;
* `sistema_gerador`: Nome e versão do software utilizado para operar o
  Programa de Gestão e gerar os dados enviados. Exemplo: "Petrvs 2.1".


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
3 poderá enviar dados diretamente para API. Deve corresponder à
instituição com poder de autorização. Ou seja, ainda que tenha optado por
usar antigas portarias ministeriais de autorização, é hoje a UORG
responsável pelo envio dos dados.

Exemplo: "Ministério da Gestão e da Inovação em Serviços Públicos" ou
"Conselho de Controle de Atividades Financeiras"

Caso seja um unidade de nível maior que Lv1, deve-se informar o código
de 14 dígitos - Código do órgão e código da Unidade Organizacional (Uorg)
no sistema Siape. Os cinco primeiros dígitos correspondem ao Órgão e os
nove últimos correspondem a Uorg.

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
  * `4`: Teletrabalho com Residência no Exterior (Dec.11.072/2022, art. 12, VIII)
  * `5`: Teletrabalho com Residência no Exterior (Dec.11.072/2022, art. 12, §7°)
* A `data_assinatura_tcr` não pode ser data futura. Recomenda-se enviar
  no formato ISO 8601 para datas (YYYY-MM-DD).
* A `data_assinatura_tcr` não pode ser inferior a 31/07/2023.
* A `data_assinatura_tcr` deve permanecer a data original, mesmo em caso de haver repactuação.

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
* É obrigatório o envio dos planos nos status "3", "4" e "5". Os planos nos
  demais status não precisam necessariamente ser enviados.
* A avaliação do plano de entregas pelo nível hierárquico superior ao da chefia
  da unidade de execução deve ser de até trinta dias após o término do plano de entregas.
* O campo `avaliacao` admite valores de `1` a `5`:
  * `1`: excepcional: plano de entregas executado com desempenho muito acima do esperado;
  * `2`: alto desempenho: plano de entregas executado com desempenho acima do esperado;
  * `3`: adequado: plano de entregas executado dentro do esperado;
  * `4`: inadequado: plano de entregas executado abaixo do esperado;
  * `5`: plano de entregas não executado

**Atenção:** os Planos de Entrega devem ser enviados antes dos Planos de
Trabalho.


#### 2.1. Entrega

* Os valores `id_entregas` devem ser únicos dentro do mesmo Plano de Entregas.
* O campo `meta_entrega` tem que ser um inteiro maior ou igual a zero.
* Para o campo `tipo_meta` são permitidos os seguintes valores:
  * `unidade`
  * `percentual`

**Atenção:** não é permitido o envio do Plano de Entregas sem entregas, exceto
se o status do Plano de Entrega for igual a 1 (Cancelado).

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
* Para o campo `status` são permitidos os seguintes valores:
  * `1`: Cancelado;
  * `2`: Aprovado;
  * `3`: Em execução;
  * `4`: Concluído;
*  O status "2" refere-se ao inciso II do art. 17 da IN nº 24/2023, ou seja,
   com a pactuação entre chefia e participante do plano de trabalho. O status "3"
   refere-se ao art. 20 da IN SEGES-SGPRT/MGi nº 24/2022 O status "4" (Concluído)
   indica que os registros de execução do plano de trabalho foram inseridos e
   encaminhados para avaliação. É obrigatório o envio dos planos nos status "3" e "4".
   Os planos nos demais status não precisam necessariamente ser enviados.
* A `data_inicio` não pode ser inferior a 31/07/2023.

**Atenção:** não é permitido o envio do Plano de Trabalho sem contribuições, exceto
se o status do Plano de Trabalho for igual a 1 (Cancelado).

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
* O campo `avaliacao_registros_execucao` admite valores de `1` a `5`:
  * `1`: excepcional: plano de trabalho executado muito acima do esperado;
  * `2`: alto desempenho: plano de trabalho executado acima do esperado;
  * `3`: adequado: plano de trabalho executado dentro do esperado;
  * `4`: inadequado: plano de trabalho executado abaixo do esperado ou parcialmente executado;
  * `5`: não executado: plano de trabalho integralmente não executado.
* A `data_avaliacao_registros_execucao` deve ser igual ou posterior à
  `data_inicio_periodo_avaliativo` e não pode ser superior à data
  de envio.


-------

Para comunicar erros na aplicação e interagir com a equipe de
desenvolvimento
[acesse aqui](https://github.com/gestaogovbr/api-pgd/issues).
