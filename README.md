# SJSU RideShare

Production-grade carpooling platform for SJSU students.

## Tech Stack

- **Backend:** FastAPI (Python 3.11+) - Microservices Architecture
- **Database:** PostgreSQL 15 + Redis 7
- **Mobile:** React Native + Expo
- **Hosting:** Docker / Railway
- **External Services:** Google Maps, Stripe, SendGrid

## Prerequisites

- Python 3.11+ (or Docker)
- Docker Desktop
- Node.js (for mobile app)

## Quick Start (Backend)

1. **Start Services:**
   ```bash
   cd backend
   docker-compose up -d
   ```

2. **Verify Health:**
   - User Service: http://localhost:8001/api/v1/health

## Architecture
This project uses a microservices architecture:
- **User Service:** Authentication & Profiles
- **Ride Service:** Ride Posting & Search
- **Booking Service:** Reservation Management
- **Notification Service:** Email & Push Notifications
- **Tracking Service:** Real-time Location Updates
