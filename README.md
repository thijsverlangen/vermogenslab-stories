# vermogenslab-stories

Werkmap van de dagelijkse nieuws-story van Verlangen Finance (Instagram en Facebook).

- `slides/` de gerenderde story-slides; Buffer haalt ze hier op via de publieke raw-URL.
- `state/state.json` de opties van vandaag en de keuzestatus.
- `state/geplaatst.json` eerder geplaatste onderwerpen, tegen herhaling.
- `state/update_story.json` datum van de laatste planner-update die een update-story kreeg (routine update-story, `scripts/update_story.py`).
- `slides/update-*.png` de update-story's; bron is de publieke changelog op vermogenslab.nl/updates.
- `scripts/` slide renderen, feeds ophalen, Slack en Buffer.
- `fonts/` Nunito Sans (SIL Open Font License, zie `fonts/OFL.txt`).

Tokens staan nooit in deze repository; de routines geven ze mee als omgevingsvariabele.
