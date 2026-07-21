# NeuroVoice AI — Literaturrecherche Sprachbiomarker
Stand: 2026-07-21

## Analogie zu EEG (Ausgangspunkt der Recherche)

| EEG-Konzept | Sprach-Äquivalent |
|---|---|
| Spektralanalyse (Frequenzbänder) | Formantenanalyse (F1-F4), Spektrale Neigung, MFCCs |
| Amplitude/Spannung | Intensität/Loudness, Shimmer (Amplitudenperturbation) |
| Grundrhythmus/Frequenz | F0 (Grundfrequenz, "Tonhöhe"), Jitter (F0-Perturbation) |
| Signalrauschen/Artefakt | Harmonics-to-Noise-Ratio (HNR), Noise-to-Harmonics (NHR) |
| Zeitliche Muster (z.B. K-Komplexe) | Pausenmuster, Sprechrate, Diadochokinese-Rate |
| Nichtlineare Dynamik (Entropie etc.) | RPDE, DFA, PPE (nichtlineare Stimm-Dynamik-Maße) |

## Feature-Kategorien (aus der Literatur konsolidiert)

### 1. Phonation / Stimmbandebene (Larynx)
- **F0 (Grundfrequenz)**: Mittelwert + Standardabweichung. SD(F0) = "Monopitch"-Maß — bei PD typischerweise reduziert.
- **Jitter**: Zyklus-zu-Zyklus-Schwankung der Grundfrequenz (Stimmband-Unregelmäßigkeit).
- **Shimmer**: Zyklus-zu-Zyklus-Schwankung der Amplitude.
- **HNR / NHR**: Verhältnis harmonischer zu Rausch-Energie — Maß für Stimmbandschluss-Qualität (Heiserkeit, Behauchtheit).
- **Nichtlineare Dynamik-Maße**: RPDE (Recurrence Period Density Entropy), DFA (Detrended Fluctuation Analysis), PPE (Pitch Period Entropy) — etabliert v.a. in der klassischen Parkinson-Stimm-Literatur (Little/Tsanas-Datensätze).
- **CPP (Cepstral Peak Prominence)**: gilt in neueren Arbeiten als robuster als Jitter/Shimmer bei fließender Sprache (Jitter/Shimmer funktionieren nur bei gehaltenem Vokal zuverlässig).

### 2. Spektralanalyse / Klangfarbe
- **Formanten F1-F3**: Resonanzfrequenzen des Vokaltrakts — F1 korreliert mit Zungenhöhe (offen/geschlossen), F2 mit Zungenposition vorne/hinten.
- **Vowel Space Area (VSA)** / **Formant Centralization Ratio (FCR)**: Fläche, die die Eckvokale (i/a/u) im F1-F2-Raum aufspannen. Reduzierte VSA = "zentralisierte" Vokale = typisch für hypokinetische Dysarthrie (PD). Aber: umstritten, hohe intersubjektive Varianz — Formant-*Ratios* gelten als sensitiver als reine Flächenmaße.
- **MFCCs (Mel-Frequency Cepstral Coefficients)**: Standard-Klangfarben-Repräsentation, Basis vieler ML-Modelle.
- **Spectral Slope/Tilt, Alpha Ratio, Hammarberg Index**: Verhältnis Energie hoher vs. tiefer Frequenzen — verändert sich mit Stimmqualität/Anstrengung.

### 3. Artikulation
- **Ort der Artikulation ist spektral unterscheidbar**: velare Laute (hinterer Gaumen, z.B. /k/,/g/) zeigen kompakte Energie ~1800-2000 Hz, F2-Übergänge ~1000-1500 Hz (durch verlängerten vorderen/verkürzten hinteren Rachenraum). Alveolare Laute (z.B. /t/,/d/,/s/) zeigen breitbandige Energie >4000 Hz.
- **VOT (Voice Onset Time)**: Zeit zwischen Verschlusslösung und Stimmbandeinsatz bei Plosiven — verlängert/unregelmäßig bei Dysarthrie.
- **Diadochokinetische Rate (DDK)**: Wiederholungsrate von Silben wie "pa-ta-ka" — Standardaufgabe für Artikulationsgeschwindigkeit/-regelmäßigkeit. Bei PD: verlangsamt + unregelmäßiger.

### 4. Prosodie (Sprachmelodie/Betonung)
- **Monopitch**: reduzierte F0-Variabilität (SD F0 über Äußerung) — eines der robustesten PD-Merkmale.
- **Monoloudness**: reduzierte Intensitätsvariabilität.
- **Rhythmus/PVI (Pairwise Variability Index)**: Maß für Silbendauer-Variabilität — Sprachrhythmus "eintönig" vs. "lebendig".
- Auch bei Autismus-Spektrum-Störungen und anderen neurologischen Bildern verändert (nicht PD-spezifisch, aber Muster unterscheiden sich).

### 5. Zeitliche Struktur / Sprechfluss
- **Sprechrate (Net Speech Rate)**: Silben/Wörter pro Zeiteinheit exklusive Pausen.
- **Pausenmuster**: Anzahl, Dauer, Position der Pausen (Duration of Pause Intervals). Verlängerte/häufigere Pausen = robuster PD-Marker.
- **Atemmuster vor Sprache**: unregelmäßige/zu tiefe Einatmung vor Sprechbeginn bei PD beschrieben (schwieriger zu erfassen ohne Zusatzsensorik, aber teils aus Audio ableitbar über Atemgeräusche).

### 6. Stimmklang / Geschlecht / Grundcharakteristik
- F0-Bereich unterscheidet sich stark nach Geschlecht (grob: Frauen ~165-255 Hz, Männer ~85-155 Hz) — jede Analyse-Pipeline braucht Normalisierung/Referenzwerte pro Sprecher:in, sonst verzerren Geschlechtsunterschiede die longitudinale Auswertung.
- Manche ML-Studien klassifizieren PD-Onset getrennt nach Geschlecht, weil Genauigkeit sonst schlechter ist (z.B. 89% männlich vs. 70% weiblich in einer zitierten Studie) — spricht dafür, Geschlecht/Referenzbereich von Anfang an als Metadatum zu erfassen.

## Etablierte Feature-Sets & Open-Source-Tools

- **GeMAPS / eGeMAPS** (Eyben et al., Geneva Minimalistic Acoustic Parameter Set): De-facto-Standard in Voice-Research/Affective Computing. eGeMAPS = 88 Features (F0, Jitter, Formanten, Shimmer, Loudness, HNR, Spectral Slope, Hammarberg-Index, zeitliche Merkmale). Guter, breit akzeptierter Startpunkt, nicht PD-spezifisch aber vollständig.
- **openSMILE**: Referenzimplementierung für GeMAPS/eGeMAPS, C++/Python, Industriestandard, gut dokumentiert, aktiv gepflegt (audEERING).
- **Parselmouth**: Python-Wrapper um Praat — gibt Zugriff auf alle klinisch validierten Praat-Analysen (Pitch, Jitter, Shimmer, HNR, Formanten, Pausenerkennung) direkt in Python. Für ein klinisch-orientiertes Tool evtl. der bessere Fit als reines openSMILE, weil Praat in der Sprachpathologie der etablierte Goldstandard ist.
- **DisVoice**: Python-Bibliothek, explizit für klinische/pathologische Sprachanalyse entwickelt (Phonation, Artikulation, Prosodie, Sprechfluss als vorgefertigte Module) — direkt auf Parkinson/Dysarthrie-Use-Cases zugeschnitten.

## Wichtige Einschränkungen aus der Literatur (nicht ignorieren)

1. **Jitter/Shimmer sind nur bei gehaltenem Vokal ("aaa") zuverlässig** — bei Fließsprache/Lesetext unbrauchbar bzw. instabil. → CPP ist hier robuster. Das beeinflusst direkt, welches Feature zu welchem Task-Typ (Vokal vs. Freisprache vs. Lesetext) gehört.
2. **VSA/Formant-Flächenmaße sind uneinheitlich validiert** — hohe Sprecher-zu-Sprecher-Varianz, manche Studien finden keine signifikanten Unterschiede. Formant-*Ratios* gelten als robuster.
3. **Automatisierte Metriken korrelieren nicht immer mit dem, was Kliniker*innen perzeptiv hören** — Diskrepanz zwischen "objektiver Zahl" und wahrgenommener Stimmqualität ist in der Literatur dokumentiert, sollte im Tool nicht verschwiegen werden (z.B. durch Konfidenz-/Warnhinweise statt reiner Zahlenausgabe).
4. **Geschlechts-/Alters-Normalisierung ist Pflicht**, sonst sind longitudinale Trends nicht von Populationsunterschieden zu trennen.

## Sprachspezifik: Deutsch (Muttersprache des Projekts)

- **Fortis/Lenis-Kontrast bei Plosiven (p/b, t/d, k/g)**: Im Deutschen primär über
  **Verschlussdauer** signalisiert (Fortis ca. 4x länger als Lenis), nicht über Aspiration/VOT
  wie im Englischen — beide Typen sind im Deutschen weitgehend unaspiriert. Zusätzlich F0-Effekte
  am Vokaleinsatz nach dem Plosiv. Konsequenz: VOT als alleiniges Artikulations-Feature (Stufe 5)
  ist für Deutsch nicht das primäre Maß — Verschlussdauer muss ergänzt/priorisiert werden.
- **Saarbrücken Voice Database (SVD)**: 2225 deutsche Sprecher:innen (869 gesund, 1356 mit 71
  Pathologien), gehaltene Vokale /a/, /i/, /u/ in vier Tonlagen (normal/hoch/tief/steigend-fallend).
  Größte frei verfügbare deutsche Normwert-Basis für Phonation-Features (F0, Jitter, Shimmer, HNR) —
  sinnvoll als Referenzpunkt statt eigene Normwerte von Grund auf zu erheben.
- **"Nordwind und Sonne"**: IPA-Standardreferenztext, in nahezu jeder Sprache in einer
  Standardversion vorhanden, phonetisch repräsentativ — gewählt als Lesetext für den
  "Lesetext"-Task-Typ (siehe docs/lesetext_nordwind_sonne.md).

## Quellen (Auswahl)

- [Analysis of Voice, Speech, and Language Biomarkers of Parkinson's Disease Collected in a Mixed Reality Setting](https://www.mdpi.com/1424-8220/25/8/2405)
- [Speech Markers of Parkinson's Disease: Phonological Features and Acoustic Measures](https://www.mdpi.com/2076-3425/15/11/1162)
- [Exploring digital speech biomarkers of hypokinetic dysarthria in a multilingual cohort](https://www.sciencedirect.com/science/article/abs/pii/S174680942301100X)
- [Vocal Feature Changes for Monitoring Parkinson's Disease Progression—A Systematic Review](https://pmc.ncbi.nlm.nih.gov/articles/PMC11939921/)
- [Speech and language biomarkers for Parkinson's disease prediction, early diagnosis and progression](https://www.nature.com/articles/s41531-025-00913-4)
- [Vowel production: a potential speech biomarker for early detection of dysarthria in Parkinson's disease](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10493417/)
- [The Geneva Minimalistic Acoustic Parameter Set (GeMAPS) for Voice Research and Affective Computing](https://mediatum.ub.tum.de/doc/1523509/file.pdf)
- [Vocal Acoustic Analysis – Jitter, Shimmer and HNR Parameters](https://www.sciencedirect.com/science/article/pii/S2212017313002788)
- [Jitter vs Shimmer in Voice Analysis](https://www.phonalab.com/en/guides/posts/jitter-shimmer-explained)
- [Automated Vowel Articulation Analysis in Connected Speech Among Progressive Neurological Diseases](https://pubmed.ncbi.nlm.nih.gov/37499137/)
- [Articulatory-Acoustic Vowel Space: Application to Clear Speech in Individuals with Parkinson disease](https://www.researchgate.net/publication/263858171_Articulatory-Acoustic_Vowel_Space_Application_to_Clear_Speech_in_Individuals_with_Parkinson_disease)
- [Exploration of Metrics for Quantifying Formant Space: Implications for Clinical Assessment of Parkinson Disease](https://pubs.asha.org/doi/10.1044/2019_PERS-SIG19-2018-0004)
- [Acoustic assessment in Mandarin-speaking Parkinson's disease patients](https://www.nature.com/articles/s41531-024-00720-3)
- [Effects of speech rate modifications on phonatory acoustic outcomes in Parkinson's disease](https://pmc.ncbi.nlm.nih.gov/articles/PMC10914948/)
- [(Dys)Prosody in Parkinson's Disease](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8392525/)
- [Prosody in Parkinson's Disease | ASHA Perspectives](https://pubs.asha.org/doi/abs/10.1044/nnsld19.3.77)
- [Acoustic structure of consonants (Oxford Phonetics)](https://www.phon.ox.ac.uk/jcoleman/consonant_acoustics.htm)
- [Open-source packages for using speech data in ML — DrivenData](https://blog.drivendata.org/blog/speech-for-ml)
- [openSMILE — The Munich Versatile and Fast Open-Source Audio Feature Extractor](https://www.researchgate.net/publication/224929655_openSMILE_--_The_Munich_Versatile_and_Fast_Open-Source_Audio_Feature_Extractor)
- [GitHub: hyyoka/Acoustic-Features (parselmouth, librosa, disvoice)](https://github.com/hyyoka/Acoustic-Features)
- [Comparative Evaluation of Acoustic Feature Extraction Tools for Clinical Speech (Interspeech 2025)](https://www.isca-archive.org/interspeech_2025/choi25h_interspeech.pdf)
- [Obstruent voicing effects on F0, but without voicing: Phonetic correlates of Swiss German lenis, fortis, and aspirated stops](https://www.sciencedirect.com/science/article/abs/pii/S0095447017302681)
- [Nordwind und Sonne — IMS Uni Stuttgart (Standardtext Deutsch)](https://www2.ims.uni-stuttgart.de/sgtutorial/nordwind.html)
- [Nordwind und Sonne in 76 Mundarten — Phonogrammarchiv Uni Zürich](https://www.phonogrammarchiv.uzh.ch/de/Nordwind-und-Sonne.html)
