O **Programa de Gestão** é a política da Administração Pública Federal para ...

Esta API permite que órgãos federais submetam os Planos de Trabalhos da sua força de trabalho para a SEGES/ME.

Para solicitar credenciais para submissão de dados, entre em contato com [email-de-apoio@economia.gov.br](mailto:email-do-suporte@economia.gov.br)

-------

Os **Planos de Trabalhos** submetidos devem seguir as seguintes regras:
* O `cod_plano` deve ser único para cada Plano de Trabalho.
* Ao utilizar o método PUT do Plano de Trabalho, o `cod_plano` que compõe a URL deve ser igual ao fornecido no JSON.
* A `data_inicio` do Plano de Trabalho deve ser menor ou igual à `data_fim`.
* A `data_avaliacao` da atividade deve ser maior ou igual que a `data_inicio` do Plano de Trabalho.
* As atividades de um mesmo Plano de Trabalho devem possuir `id_atividade` diferentes.
* O `cpf` deve possuir exatamente 11 dígitos e sem máscaras.
* Valores permitidos para a `modalidade_execucao`:
  * **1** - Presencial
  * **2** - Semipresencial
  * **3** - Teletrabalho
* `carga_horaria_semanal` deve ser entre 1 e 40.
* Os campos `quantidade_entregas`, `quantidade_entregas_efetivas`, `tempo_exec_presencial`, `tempo_exec_teletrabalho` da Atividade e `horas_homologadas` do Plano de Trabalho devem ser maiores que zero.
* `entregue_no_prazo` não é obrigatório e deve ser `True` ou `False` caso esteja preenchido.
* Explore a seção [**Schemas**](#model-AtividadeSchema) nesta documentação para descobrir mais detalhes e quais campos são obrigatórios para as Atividades e os Planos de Trabalho.

Para comunicar erros na aplicação e interagir com a equipe de desenvolvimento [acesse aqui](https://github.com/economiagovbr/api-pgd/issues).