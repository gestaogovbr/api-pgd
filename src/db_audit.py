AUDIT_DDL = """
    CREATE SCHEMA IF NOT EXISTS auditoria;

    CREATE TABLE IF NOT EXISTS auditoria.auditoria_db (
        id SERIAL PRIMARY KEY,
        operacao TEXT,
        tabela TEXT,
        registro_antigo JSONB,
        registro_novo JSONB,
        usuario TEXT,
        data_operacao TIMESTAMPTZ DEFAULT now()
    );

    CREATE OR REPLACE FUNCTION auditoria.fn_auditoria() RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            INSERT INTO auditoria.auditoria_db (operacao, tabela, registro_novo, usuario)
            VALUES ('INSERT', TG_TABLE_NAME, to_jsonb(NEW), current_user);

        ELSIF TG_OP = 'UPDATE' THEN
            INSERT INTO auditoria.auditoria_db (operacao, tabela, registro_antigo, registro_novo, usuario)
            VALUES ('UPDATE', TG_TABLE_NAME, to_jsonb(OLD), to_jsonb(NEW), current_user);

        ELSIF TG_OP = 'DELETE' THEN
            INSERT INTO auditoria.auditoria_db (operacao, tabela, registro_antigo, usuario)
            VALUES ('DELETE', TG_TABLE_NAME, to_jsonb(OLD), current_user);
        END IF;

        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS tr_auditoria_pt ON plano_trabalho;
    DROP TRIGGER IF EXISTS tr_auditoria_pe ON plano_entregas;
    DROP TRIGGER IF EXISTS tr_auditoria_part ON participante;
    DROP TRIGGER IF EXISTS tr_auditoria_us ON users;
    DROP TRIGGER IF EXISTS tr_auditoria_co ON contribuicao;
    DROP TRIGGER IF EXISTS tr_auditoria_en ON entrega;
    DROP TRIGGER IF EXISTS tr_auditoria_are ON avaliacao_registros_execucao;


    CREATE TRIGGER tr_auditoria_pt
    AFTER INSERT OR UPDATE OR DELETE ON plano_trabalho
    FOR EACH ROW EXECUTE FUNCTION auditoria.fn_auditoria();

    CREATE TRIGGER tr_auditoria_pe
    AFTER INSERT OR UPDATE OR DELETE ON plano_entregas
    FOR EACH ROW EXECUTE FUNCTION auditoria.fn_auditoria();

    CREATE TRIGGER tr_auditoria_part
    AFTER INSERT OR UPDATE OR DELETE ON participante
    FOR EACH ROW EXECUTE FUNCTION auditoria.fn_auditoria();

    CREATE TRIGGER tr_auditoria_us
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION auditoria.fn_auditoria();

    CREATE TRIGGER tr_auditoria_co
    AFTER INSERT OR UPDATE OR DELETE ON contribuicao
    FOR EACH ROW EXECUTE FUNCTION auditoria.fn_auditoria();

    CREATE TRIGGER tr_auditoria_en
    AFTER INSERT OR UPDATE OR DELETE ON entrega
    FOR EACH ROW EXECUTE FUNCTION auditoria.fn_auditoria();

    CREATE TRIGGER tr_auditoria_are
    AFTER INSERT OR UPDATE OR DELETE ON avaliacao_registros_execucao
    FOR EACH ROW EXECUTE FUNCTION auditoria.fn_auditoria();
"""