SELECT * FROM "Bulgarian_import"."4" WHERE "Месец" >= DATE '2021-01-01' AND "Месец" < DATE '2026-01-01' AND upper(btrim("МКБ")) ~ '^I[0-9]{2}([.]|$)' ORDER BY "Месец", "МКБ" ;
