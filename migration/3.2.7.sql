-- Migra o esquema do banco de dados da versão 3.2.6 para a versão 3.2.7

BEGIN;

ALTER TABLE avaliacao_registros_execucao
ALTER COLUMN cod_unidade_autorizadora_pt TYPE bigint;

ALTER TABLE contribuicao
ALTER COLUMN cod_unidade_autorizadora_pt TYPE bigint;

ALTER TABLE entrega
ALTER COLUMN cod_unidade_autorizadora TYPE bigint;

ALTER TABLE participante
ALTER COLUMN cod_unidade_autorizadora TYPE bigint,
ALTER COLUMN cod_unidade_lotacao TYPE bigint,
ALTER COLUMN cod_unidade_instituidora TYPE bigint;

ALTER TABLE plano_entregas
ALTER COLUMN cod_unidade_autorizadora TYPE bigint,
ALTER COLUMN cod_unidade_instituidora TYPE bigint,
ALTER COLUMN cod_unidade_executora TYPE bigint;

ALTER TABLE plano_trabalho
ALTER COLUMN cod_unidade_autorizadora TYPE bigint,
ALTER COLUMN cod_unidade_executora TYPE bigint,
ALTER COLUMN cod_unidade_lotacao_participante TYPE bigint;

ALTER TABLE users
ALTER COLUMN cod_unidade_autorizadora TYPE bigint;

COMMIT;
