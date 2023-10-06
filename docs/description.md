Esta API permite que órgãos federais submetam os Planos de Trabalhos da
sua força de trabalho para a SEGES/MGI. Para solicitar credenciais para
submissão de dados, entre em contato com
[pgd@economia.gov.br](mailto:pgd@economia.gov.br)

> ### Instrução Normativa Conjunta SEGES-SGPRT n.º 24, de 28 de julho de 2023
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

Explore a seção [**Schemas**](#model-AtividadeSchema) nesta documentação
para descobrir mais detalhes e quais campos são obrigatórios para as
Atividades e os Planos de Trabalho.

-------
## Gestão de Usuários

O cadastro de usuários é feito pela aplicação Fief. Para cadastrar um
novo usuário, faça o login como administrador do Fief.

Na coluna da esquerda, selecione a opção "Users". Clique o botão
vermelho "add new user". Digite o e-mail e a senha do usuário, bem como
o código SIAPE da unidade instituidora do PGD, para a qual será realizada
a carga dos dados.

(detalhar mais, possivelmente mover para página separada colocando link
aqui, incluir imagens de tela)

-------
## Endpoints

A API consiste em três endpoints principais.

Como algumas entidades fazem referência a outras, as que são referenciadas
precisam ser enviadas primeiro. Por isso, os dados devem ser enviados
na seguinte ordem:

1. Participantes
2. Planos de Entrega
3. Planos de Trabalho

### Planos de Entregas

Os **Planos de Entregas** representam as entregas previstas para aquela
unidade no âmbito do Programa de Gestão. Eles devem seguir as seguintes
regras:

* Não deve haver sobreposição de intervalos (`data_inicio_plano_entregas`
  e `data_termino_plano_entregas`) entre diferentes Planos de Entrega na
  mesma unidade (`cod_SIAPE_unidade_plano`).

**Atenção:** os Planos de Entrega devem ser enviados antes dos Planos de
Trabalho.

#### Entrega

* Para o campo `tipo_meta` são permitidos os seguintes valores:
  * `1`: absoluto
  * `2`: percentual

### Planos de Trabalho

Os **Planos de Trabalhos** submetidos devem seguir as seguintes regras:
* O `id_plano_entrega_unidade` deve ser único para cada Plano de Trabalho.
* Ao utilizar o método PUT do Plano de Trabalho, o
  `id_plano_entrega_unidade` que compõe a URL deve ser igual ao fornecido
  no JSON.
* A `data_inicio_plano` do Plano de Trabalho deve ser menor ou igual à
  `data_termino_plano`.

#### Contribuição

* (... complementar)


#### Consolidação

* A `data_inicio_registro` da consolidação deve ser maior ou igual que a
  `data_inicio_plano` do Plano de Trabalho.
* (... complementar)


### Participante

* O `cpf_participante` deve possuir exatamente 11 dígitos e sem máscaras.
* Valores permitidos para a `modalidade_execucao`:
  * **1** - Presencial
  * **2** - Semipresencial
  * **3** - Teletrabalho
* `carga_horaria_semanal` deve ser entre 1 e 40.
* Os campos `quantidade_entregas`, `quantidade_entregas_efetivas`,
  `tempo_exec_presencial`, `tempo_exec_teletrabalho` da Atividade e
  `horas_homologadas` do Plano de Trabalho devem ser maiores que zero.
* `entregue_no_prazo` não é obrigatório e deve ser `True` ou `False`
  caso esteja preenchido.

-------

Para comunicar erros na aplicação e interagir com a equipe de
desenvolvimento
[acesse aqui](https://github.com/gestaogovbr/api-pgd/issues).
