```markdown
# Dicionário Técnico do Contrato de Dados: tb_contratos_credito

## Informações do Contrato
- **Nome do Contrato:** Contratos de produtos de crédito ativos e encerrados.
- **Proprietário:** Squad Credito
- **Versão:** 3.0.0
- **Status:** DRAFT
- **Fonte:** Sistema de Crédito SAS (SISTEMA_CREDITO_SAS), formato sas7bdat, codificação latin-1, sistema Unix, atualização diária.
- **Contato:** squad-credito@banco.com.br

## Business Context
- Os dados representam contratos de crédito para todos os produtos ofertados pelo banco.
- Os dados são utilizados mensalmente para o Sistema de Controle de Crédito (SCR).

## Colunas e Descrições

1. **id_contrato (cd_id_contrato):** Identificador único do contrato gerado pelo sistema de crédito.
   - **Propósito:** Identificação exclusiva para cada contrato.
   - **Tipo:** STRING
   - **Comportamento esperado:** Único para cada contrato.

2. **cd_cliente:** Referência ao cliente em tb_clientes.
   - **Propósito:0000000000000000000000000000000

---
> **[AI_METADATA_STATUS: DRAFT]**