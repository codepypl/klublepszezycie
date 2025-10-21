-- Naprawa tokenów w password_reset_tokens przed migracją
-- Wykonaj to na produkcji przed uruchomieniem flask db upgrade

-- 1. Sprawdź aktualny stan
SELECT 
    LENGTH(token) as token_length,
    COUNT(*) as count
FROM password_reset_tokens 
GROUP BY LENGTH(token)
ORDER BY token_length;

-- 2. Sprawdź czy są tokeny dłuższe niż 36 znaków
SELECT COUNT(*) as long_tokens_count
FROM password_reset_tokens 
WHERE LENGTH(token) > 36;

-- 3. Jeśli są tokeny dłuższe niż 36 znaków, skróć je
UPDATE password_reset_tokens 
SET token = LEFT(token, 36)
WHERE LENGTH(token) > 36;

-- 4. Sprawdź aktualną długość kolumny
SELECT character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'password_reset_tokens' 
AND column_name = 'token';

-- 5. Jeśli kolumna nie ma długości 36, zmień ją
-- (Uwaga: to może nie działać jeśli są tokeny dłuższe niż 36)
ALTER TABLE password_reset_tokens 
ALTER COLUMN token TYPE VARCHAR(36);

-- 6. Utwórz indeks (jeśli nie istnieje)
CREATE UNIQUE INDEX IF NOT EXISTS ix_password_reset_tokens_token 
ON password_reset_tokens (token);

-- 7. Sprawdź końcowy stan
SELECT 
    LENGTH(token) as token_length,
    COUNT(*) as count
FROM password_reset_tokens 
GROUP BY LENGTH(token)
ORDER BY token_length;
