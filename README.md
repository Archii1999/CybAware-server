# CybAware API

CybAware is een FastAPI-backend voor gebruikersbeheer, authenticatie en beveiligde toegang tot e-learningmodules over cybersecurity in de zorg (NEN 7510).  
De huidige versie bevat JWT-authenticatie, role-based access, filtering, paginatie en veilige wachtwoordopslag.

---

## Functionaliteiten

- JWT-authenticatie met access tokens
- Role-based access control (admin / user)
- CRUD-functionaliteit voor gebruikers
- Paginatie en filtering in het gebruikersoverzicht
- Versleutelde wachtwoordopslag (bcrypt)
- Modulaire projectstructuur voor uitbreiding

---

## Projectstructuur

app/
├── main.py # startpunt van de API
├── core/
│ └── config.py # instellingen en .env-configuratie
├── database.py # databaseconnectie
├── models.py # SQLAlchemy-modellen
├── security.py # hashing + JWT-logica
├── deps.py # dependencies (auth/db)
├── routers/
│ ├── auth.py # login & /me endpoints
│ └── users.py # gebruikersbeheer
└── schemas/
├── auth.py # schemas voor login/token
└── users.py # schemas voor user input/output
