# Football Club Platform - Documentazione

Documentazione completa del progetto Football Club Platform.

## Struttura Documentazione

### 📐 Architettura
- [**ARCHITECTURE.md**](architecture/ARCHITECTURE.md) - Architettura generale del sistema
- [**PROJECT_SUMMARY.md**](architecture/PROJECT_SUMMARY.md) - Riepilogo del progetto
- [**NAMING_CONVENTION.md**](architecture/NAMING_CONVENTION.md) - Convenzioni di nomenclatura

### 🔧 Sviluppo
- [**IMPLEMENTATION_STATUS.md**](development/IMPLEMENTATION_STATUS.md) - Stato implementazione features
- [**MIGRATION_GUIDE.md**](development/MIGRATION_GUIDE.md) - Guida alle migrazioni database
- [**IMPLEMENTAZIONE_COMPLETA.md**](development/IMPLEMENTAZIONE_COMPLETA.md) - Dettagli implementazione completa

### 🚀 Operations
- [**OPERATIONS.md**](operations/OPERATIONS.md) - Guida operativa (deploy, backup, monitoring)
- [**DEPLOYMENT_REPORT.md**](operations/DEPLOYMENT_REPORT.md) - Report stato deployment

### 📡 API
- [**API.md**](api/API.md) - Documentazione API endpoints
- [**ADVANCED_TRACKING_IMPLEMENTATION.md**](api/ADVANCED_TRACKING_IMPLEMENTATION.md) - API tracking avanzato
- [**PERFORMANCE_MODULES_SUMMARY.md**](api/PERFORMANCE_MODULES_SUMMARY.md) - Moduli performance

### 📊 Report & Changelog
- [**CHANGELOG_CLAUDE.md**](reports/CHANGELOG_CLAUDE.md) - Changelog modifiche
- [**CLEANUP_REPORT.md**](reports/CLEANUP_REPORT.md) - Report pulizia codebase
- [**DEEP_CLEANUP_REPORT.md**](reports/DEEP_CLEANUP_REPORT.md) - Report pulizia approfondita
- [**FOOTBALL_CLUB_PLATFORM_DIAGNOSTIC_REPORT.md**](reports/FOOTBALL_CLUB_PLATFORM_DIAGNOSTIC_REPORT.md) - Report diagnostico

## Quick Start

1. **Setup Ambiente**
   ```bash
   # Copia configurazione
   cp .env.example .env

   # Avvia stack Docker
   make up

   # Esegui migrazioni
   make migrate
   ```

2. **Accedi alla Documentazione API**
   - Swagger UI: http://localhost:8101/docs
   - ReDoc: http://localhost:8101/redoc

3. **Accedi al Frontend**
   - Frontend: http://localhost:3101

## Requisiti Sistema

- Docker 20.10+
- Docker Compose 2.0+
- Make (opzionale ma consigliato)

## Supporto

Per problemi o domande, consulta [OPERATIONS.md](operations/OPERATIONS.md) o apri una issue.
