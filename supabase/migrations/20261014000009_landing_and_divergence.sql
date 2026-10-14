-- ============================================================================
-- FASE 9: LANDING PAGE INSTITUCIONAL, PREVENÇÃO DE DIVERGÊNCIA CADASTRAL
-- E PERSONALIZAÇÃO DE MENSAGENS DE AGRADECIMENTO
-- ============================================================================

-- 1. Extensão da tabela de condomínios com configurações da Landing Page e mensagem padrão
ALTER TABLE app.condominiums
ADD COLUMN IF NOT EXISTS landing_title VARCHAR(255),
ADD COLUMN IF NOT EXISTS landing_subtitle VARCHAR(255),
ADD COLUMN IF NOT EXISTS landing_description TEXT,
ADD COLUMN IF NOT EXISTS landing_contact_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS landing_contact_phone VARCHAR(50),
ADD COLUMN IF NOT EXISTS default_thank_you_message TEXT;

-- 2. Extensão da tabela de consultas públicas com mensagem de agradecimento customizada
ALTER TABLE app.public_consultations
ADD COLUMN IF NOT EXISTS thank_you_message TEXT;

-- 3. Extensão da tabela de sugestões de consultas com sinalização de divergência cadastral
ALTER TABLE app.consultation_suggestions
ADD COLUMN IF NOT EXISTS has_divergence BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS divergence_details TEXT,
ADD COLUMN IF NOT EXISTS registered_email VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_consultation_suggestions_divergence 
ON app.consultation_suggestions(has_divergence);
