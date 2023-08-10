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
### Usuários
* Para geração de uma nova senha de usuário, utilizar o método `Forgot Password`.
Um token será encaminhado ao email cadastrado para geração da nova senha.
Em seguida, acessar o método `Reset Password`, informando o token e a nova
senha.

* Alteração de dados de usuário deve ser realizada pelo superusuário
através do método `Update User`. Informar no **Request Body** somente os
dados que devem ser alterados (caso informe um email já existente o sistema
retornará erro).

-------
### Planos de Trabalho
Os **Planos de Trabalhos** submetidos devem seguir as seguintes regras:
* O `cod_plano` deve ser único para cada Plano de Trabalho.
* Ao utilizar o método PUT do Plano de Trabalho, o `cod_plano` que
  compõe a URL deve ser igual ao fornecido no JSON.
* A `data_inicio` do Plano de Trabalho deve ser menor ou igual à `data_fim`.
* A `data_avaliacao` da atividade deve ser maior ou igual que a
  `data_inicio` do Plano de Trabalho.
* As atividades de um mesmo Plano de Trabalho devem possuir
  `id_atividade` diferentes.
* O `cpf` deve possuir exatamente 11 dígitos e sem máscaras.
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


Para comunicar erros na aplicação e interagir com a equipe de
desenvolvimento
[acesse aqui](https://github.com/gestaogovbr/api-pgd/issues).
