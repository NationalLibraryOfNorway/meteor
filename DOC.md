## Kilde for metadata verdier

Dataene er ekstrahert fra 2 kilder:

- _pdfinfo_: metadata som er embedded i PDF-filen.
- _tekst_: tekstelementene fra de 5 første og 5 siste sidene av dokumentet.

### Tittel

Tittelen er hentet fra:

- "title" fra _pdfinfo_, om den også finnes noe sted i _tekst_
- _tekst_-blokka som er skrevet med største font på første side
- _tekst_ som står ved en "tittel"-blokk på en kolofon- eller informasjonsside

### År

År-verdien er hentet fra 3 forskjellige kilder (synkende rekkefølge for preferanse):

- en copyright-linje i teksten (f. eks. "© NAV 2016")
- "modDate" fra _pdfinfo_ (datoen når filen sist ble endret), hvis datoen også finnes i _tekst_
- "creationDate" fra _pdfinfo_ (datoen når filen ble opprettet), hvis datoen også finnes i _tekst_

### ISBN/ISSN

Vi søker etter kombinasjoner av sifre, bindestrek og 'X' (til ISSN), med riktig format, i nærheten av ordet "ISBN"/"ISSN". I tilfeller hvor det finnes flere verdier, typisk til trykt/digital versjoner, foretrekker METEOR den digitale.

NB: per nå har vi ingen validering som sikrer at ISBN/ISSN-verdien er gyldig.

### Utgiver

For å finne utgivere, bruker vi data fra [Felles autoritetsregister](https://bibsys-almaprimo.hosted.exlibrisgroup.com/primo-explore/search?vid=AUTREG).

Vi prøver å finne utgivere fra (synkende rekkefølge for preferanse):

- _tekst_ som er i nærheten av "Utgiver", "Utgitt av"... (på engelsk, bokmål og nynorsk), i _tekst_
- prefiks for "-rapport" (f.eks. "NIBIO-Rapport") i _tekst_
- en copyright-linje i teksten (f. eks. "© NAV 2016")

For hvert treff returnerer METEOR den foretrukne navneformen fra autoritetsregisteret.

### Forfatter

METEOR leter etter forfatter fra tre kilder:

- metadata-felt for forfatter(e) i _pdfinfo_ hvis de finnes i _tekst_
- _tekst_ som er i nærheten av en blokk med nøkkelord som "Forfatter", "Author" på informasjonssiden (på engelsk, bokmål og nynorsk)
- _tekst_ som er på den aller første siden i dokumentet


Videre valideres teksten fra kildene opp mot følgende kriterier:

- Består av minst 2 ord
- Kan ha forkortelser av navn så lenge de er skrevet med stor bokstav (f.eks. "Edgar A. Poe")
- Kan ha bindestrek i navnet (f.eks. "Ola-Johan Nordmann")
- Kan ha apostrofer i navnet (f.eks. "John O'Leary")
- Kan ha bokstaver med diakritiske tegn utover det standarde latinske alfabetet (f.eks. Æ, Ø og Å)
- Navnet forekommer ikke i tekstblokker som inneholder ord som ikke matcher kriteriene over, med følgende unntak:
    - Ord som "and" og "og"
    - Tekst i paranteser
- Navnet forekommer ikke i tittelen
- Navnet kommer ikke etter "Fotograf:" eller varianter av dette

For å unngå at tekster som ikke er forfatternavn – men som likevel matcher kriteriene over – blir lagt til, sjekker vi også om teksten forekommer i en liste over ord som ofte forekommer i offentlige dokumenter. Eksempelvis vil ord som "Norwegian University" matche kriteriene, men ordene "Norwegian" og "University" ligger i ordlista og det blir derfor ikke oppfattet som forfatternavn.

### Språk

Til gjenkjenning av språk bruker METEOR en maskinlæring metode (N-Gram-Based Text Categorization) med språk modeller fra Språkbanken ([Målfrid](https://github.com/Sprakbanken/maalfrid)).

Per nå kan METEOR bare gjenkjenne bokmål, nynorsk, norsamisk, lulesamisk, sørsamisk, og engelsk.

### Dokumenttype

METEOR prøver å finne hva slags rapport dokumenten er, med å søke på nøkkelord på forsiden. Mulige verdiene er årsrapport (_annualReport_), NOU, evaluering (_evaluation_), veileder(_guidance_), og undersøkelse(_survey_).
