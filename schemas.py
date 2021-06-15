from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError, validator, root_validator
from datetime import date
from enum import IntEnum

class AtividadeSchema(BaseModel):
    id_atividade: str = Field(
        title="id da atividade",
        description="Identificador único da atividade na unidade")
    nome_grupo_atividade: Optional[str] = Field(
        title="Nome do grupo de atividades"
    )
    nome_atividade: str = Field(
        title="Nome da atividade"
    )
    faixa_complexidade: str = Field(
        title="Faixa de complexidade",
        description="Faixa de complexidade da atividade."
    )
    parametros_complexidade: Optional[str] = Field(
        title="Parâmetros de complexidade",
        description="Parâmetros adotados para definição da faixa de "
                    "complexidade."
    )
    tempo_presencial_estimado: float = Field(
        title="Tempo presencial estimado",
        description="Tempo estimado para a execução da atividade em regime "
                    "presencial, antes da implementação do programa de "
                    "gestão. Usado como base de comparação para o "
                    "planejamento da atividade."
    )
    tempo_presencial_programado: float = Field(
        title="Tempo presencial programado",
        description="Tempo programado para a execução da atividade em regime "
                    "presencial, no âmbito do programa de gestão."
    )
    tempo_presencial_executado: Optional[float] = Field(
        title="Tempo presencial executado",
        description="Tempo de fato utilizado em regime presencial para "
                    "executar a atividade."
    )
    tempo_teletrabalho_estimado: float = Field(
        title="Tempo em teletrabalho estimado",
        description="Tempo estimado para a execução da atividade em regime "
                    "de teletrabalho. Usado como base de comparação para o "
                    "planejamento da atividade."
    )
    tempo_teletrabalho_programado: float = Field(
        title="Tempo em teletrabalho programado",
        description="Tempo programado para a execução da atividade em regime "
                    "de teletrabalho."
    )
    tempo_teletrabalho_executado: Optional[float] = Field(
        title="Tempo em teletrabalho executado",
        description="Tempo de fato utilizado em regime de teletrabalho para "
                    "executar a atividade."
    )
    entrega_esperada: Optional[str] = Field(
        title="Entregas esperadas"
    )
    qtde_entregas: int = Field(
        title="Quantidade de entregas",
        description="Quantidade de entregas que o participante deverá "
                    "realizar."
    )
    qtde_entregas_efetivas: Optional[int] = Field(
        title="Quantidade de entregas efetivas",
        description="Quantidade de entregas efetivamente realizadas."
    )
    avaliacao: Optional[int] = Field(
        title="Avaliação",
        description="Avaliação das entregas realizadas."
    )
    data_avaliacao: Optional[date] = Field(
        title="Data de avaliação"
    )
    justificativa: Optional[str] = Field(
        title="Justificativa",
        description="Texto livre para justificativas."
    )

    class Config:
        orm_mode = True

class ModalidadeEnum(IntEnum):
    presencial = 1
    semipresencial = 2
    teletrabalho = 3

class PlanoTrabalhoSchema(BaseModel):
    cod_plano: str = Field(
        title="código do Plano de Trabalho",
        description="Código SIORG da unidade organizacional. Será obtido no momento da autenticação."
        )
    matricula_siape: int = Field(
        title="Matrícula SIAPE",
        description="Matrícula SIAPE do participante."
        )
    cpf: str = Field(
        title="CPF",
        description="Cadastro da pessoa física na Receita Federal do Brasil.\n"
            "\n"
            "Deve conter apenas dígitos."
        )
    nome_participante: str = Field(
        title="Nome do participante"
        )
    cod_unidade_exercicio: int = Field(
        title="Código da Unidade de Exercício",
        description="Código SIORG da Unidade Organizacional em que o participante está em exercício."
        )
    nome_unidade_exercicio: str = Field(
        title="Nome da Unidade de Exercício",
        description="Nome SIORG da Unidade Organizacional em que o participante está em exercício."
        )
    modalidade_execucao: ModalidadeEnum = Field(
        ...,
        alias="modalidade_execucao",
        title="Modalidade de Execução do Plano",
        description="Modalidade de execução da atividade\n"
            "\n"
            "* 1: presencial;\n"
            "* 2: semipresencial;\n"
            "* 3: teletrabalho\n"
            )
    carga_horaria_semanal: int = Field(
        title="Carga Horária Semanal",
        description="Carga horária semanal do participante."
        )
    data_inicio: date = Field(
        title="Data Início",
        description="Data de início do Plano de Trabalho."
        )
    data_fim: date = Field(
        title="Data Fim",
        description="Data de fim do Plano de Trabalho."
        )
    carga_horaria_total: float = Field(
        title="Carga Horária Total"
        )
    data_interrupcao: Optional[date] = Field(
        title="Data de interrupção"
        )
    entregue_no_prazo: Optional[bool] = Field(
        title="Entregue no prazo",
        description="Indica se os produtos foram entregues no prazo."
        )
    horas_homologadas: Optional[float] = Field(
        title="Horas homologadas",
        description="Quantidade de horas homologadas."
        )
    atividades: List[AtividadeSchema] = Field(
        title="Atividades",
        description="Lista de Atividades planejadas no Plano de Trabalho."
        )

    # Validações
    @root_validator
    def data_validate(cls, values):
        data_inicio = values.get("data_inicio", None)
        data_fim = values.get("data_fim", None)
        if data_inicio > data_fim:
            raise ValueError("Data fim do Plano de Trabalho deve ser maior" \
                     " ou igual que Data de início.")
        for atividade in values.get("atividades", []):
            if getattr(atividade, "data_avaliacao", None) is not None and \
                atividade.data_avaliacao < data_inicio:
                    raise ValueError("Data de avaliação da atividade deve ser maior ou igual" \
                        " que a Data de início do Plano de Trabalho.")
        return values

    @validator("atividades")
    def valida_atividades(cls, atividades):
        ids_atividades = [a.id_atividade for a in atividades]
        duplicados = []
        for id_atividade in ids_atividades:
            if id_atividade not in duplicados:
                duplicados.append(id_atividade)
            else:
                raise ValueError("Atividades devem possuir id_atividade diferentes.")
        return atividades


    @validator("cpf")
    def cpf_validate(input_cpf):
        if not input_cpf.isdigit():
            raise ValueError("CPF deve conter apenas digitos.")

        cpf = [int(char) for char in input_cpf if char.isdigit()]
        #  Verifica se o CPF tem 11 dígitos
        if len(cpf) != 11:
            raise ValueError("CPF precisa ter 11 digitos.")

        #  Verifica se o CPF tem todos os números iguais, ex: 111.111.111-11
        #  Esses CPFs são considerados inválidos mas passam na validação dos dígitos
        if len(set(cpf)) == 1:
            raise ValueError("CPF inválido.")

        #  Valida os dois dígitos verificadores
        for i in range(9, 11):
            value = sum((cpf[num] * ((i+1) - num) for num in range(0, i)))
            digit = ((value * 10) % 11) % 10
            if digit != cpf[i]:
                raise ValueError("Digitos verificadores do CPF inválidos.")

        str_cpf = "".join([str(i) for i in input_cpf])
        return str_cpf

    @validator("carga_horaria_semanal")
    def must_be_less(cls, carga_horaria_semanal):
        if carga_horaria_semanal > 40 or carga_horaria_semanal <= 0:
            raise ValueError("Carga horária semanal deve ser entre 1 e 40")
        return carga_horaria_semanal

    class Config:
        orm_mode = True

class AtividadeUpdateSchema(BaseModel):
    id_atividade: str = Field(title="id da atividade")
    nome_grupo_atividade: Optional[str]
    nome_atividade: Optional[str]
    faixa_complexidade: Optional[str]
    parametros_complexidade: Optional[str]
    tempo_presencial_estimado: Optional[float]
    tempo_presencial_programado: Optional[float]
    tempo_presencial_executado: Optional[float]
    tempo_teletrabalho_estimado: Optional[float]
    tempo_teletrabalho_programado: Optional[float]
    tempo_teletrabalho_executado: Optional[float]
    entrega_esperada: Optional[str]
    qtde_entregas: Optional[int]
    qtde_entregas_efetivas: Optional[int]
    avaliacao: Optional[int]
    data_avaliacao: Optional[date]
    justificativa: Optional[str]

class PlanoTrabalhoUpdateSchema(BaseModel):
    """Esquema para atualização do plano de trabalho. Na atualização,
    todos os campos são opcionais, exceto cod_plano."""
    cod_plano: str
    matricula_siape: Optional[int]
    cpf: Optional[str]
    nome_participante: Optional[str]
    cod_unidade_exercicio: Optional[int]
    nome_unidade_exercicio: Optional[str]
    modalidade_execucao: ModalidadeEnum = Field(None, alias="modalidade_execucao")
    carga_horaria_semanal: Optional[int]
    data_inicio: Optional[date]
    data_fim: Optional[date]
    carga_horaria_total: Optional[float]
    data_interrupcao: Optional[date]
    entregue_no_prazo: Optional[bool] = None
    horas_homologadas: Optional[float]
    atividades: Optional[List[AtividadeUpdateSchema]] # = []
