-- Skrypt migracyjny dla tabeli event_schedule
-- Dodaje brakujące kolumny: hero_background i hero_background_type

-- Sprawdź czy kolumna hero_background istnieje, jeśli nie - dodaj ją
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'event_schedule' 
        AND column_name = 'hero_background'
    ) THEN
        ALTER TABLE event_schedule ADD COLUMN hero_background VARCHAR(500);
        RAISE NOTICE 'Kolumna hero_background została dodana';
    ELSE
        RAISE NOTICE 'Kolumna hero_background już istnieje';
    END IF;
END $$;

-- Sprawdź czy kolumna hero_background_type istnieje, jeśli nie - dodaj ją
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'event_schedule' 
        AND column_name = 'hero_background_type'
    ) THEN
        ALTER TABLE event_schedule ADD COLUMN hero_background_type VARCHAR(20) DEFAULT 'image';
        RAISE NOTICE 'Kolumna hero_background_type została dodana';
    ELSE
        RAISE NOTICE 'Kolumna hero_background_type już istnieje';
    END IF;
END $$;

-- Pokaż finalną strukturę tabeli
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'event_schedule'
ORDER BY ordinal_position;
