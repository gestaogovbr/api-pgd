Esta API permite que órgãos federais submetam os Planos de Trabalhos da sua força de trabalho para a SEGES/ME.
Para solicitar credenciais para submissão de dados, entre em contato com [pgd@economia.gov.br](mailto:pgd@economia.gov.br)

> ### Instrução Normativa Nº 65, de 30 de julho de 2020
>
> Estabelece orientações, critérios e procedimentos gerais a serem
> observados pelos órgãos e entidades integrantes do Sistema de Pessoal
> Civil da Administração Federal - SIPEC relativos à implementação de
> Programa de Gestão.
>
> Art. 16. Ao término do prazo de seis meses, período considerado como
> ambientação, os órgãos e entidades que tenham implementado o programa de
> gestão deverão:
>
> II - enviar os dados a que se refere o art. 28, revisando, se
> necessário, o mecanismo de coleta das informações requeridas pelo órgão
> central do SIPEC.
>
> Art. 28. Os órgãos disponibilizarão Interface de Programação de
> Aplicativos para o órgão central do SIPEC com o objetivo de fornecer
> informações atualizadas no mínimo semanalmente, registradas no sistema
> informatizado de que trata o art. 26, bem como os relatórios de que
> trata o art. 17.
>
> § 1º As informações de que trata o caput deverão ser divulgadas pelos
> órgãos em sítio eletrônico com, pelo menos, mas não se restringindo, as
> seguintes informações:
>
> I - plano de trabalho;
>
> II - relação dos participantes do programa de gestão, discriminados por
> unidade;
>
> III - entregas acordadas; e
>
> IV - acompanhamento das entregas de cada unidade.
>
> § 2º Apenas serão divulgadas informações não sigilosas, com base nas
> regras de transparência de informações e dados previstas em legislação.
>
> § 3º O órgão central do SIPEC emitirá documento com as especificações
> detalhadas dos dados a serem enviados e da interface de programação de
> aplicativos previstos no caput.

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
[acesse aqui](https://github.com/economiagovbr/api-pgd/issues).
