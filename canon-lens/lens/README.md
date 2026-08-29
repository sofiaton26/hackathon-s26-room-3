# lens/ — визуальные линзы поверх нарушений канона

Fan-out: одна единица контента → несколько представлений. Пока одна линза.

## `lens_map.py` — карта нарушений

Текст + нарушения → один самодостаточный HTML: текст с подсвеченными спанами
(error / warning / redaction — цветом), панель правил по пунктам канона, клик по
пункту подсвечивает и прокручивает к месту в тексте. Без внешних зависимостей.

```bash
# сам прогоняет проверку:
python canon-lens/lens/lens_map.py <файл> --canon canon-lens/canon.sostav.md -o map.html

# из готового JSON (развязка от canon-lens):
python -m canon_lens.cli check <файл> --canon canon-lens/canon.sostav.md --json > v.json
python canon-lens/lens/lens_map.py <файл> --violations v.json -o map.html
```

Вход `--violations` — контракт `canon-lens/CONTRACTS.md` (`{file, summary, violations[]}`).
Линза читает только его, никакой другой связи с модулями комнаты нет.

## Дальше (кап по времени не добраны)

- `lens_diff` — черновик → rewrite, каждая правка привязана к пункту канона;
- `lens_structure` — хук/суть/CTA для рилза, лид/кейс/FAQ/CTA для статьи.
