# 🛒 TG Web Shop
Full-stack e-commerce platform with Telegram Bot integration built using async Python technologies.

# 🚀 Features

## 👤 User Features
  * Product catalog browsing
  * Product search & filtering
  * Shopping cart
  * Order checkout
  * Order history
  * Telegram account linking

## 🤖 Telegram Bot
  * Interactive catalog
  * Inline keyboards
  * Cart management
  * Order creation
  * Pagination
  * Admin functionality

## 🛠 Admin Features
  * Product CRUD
  * Category management
  * Product image upload
  * Stock management
  * Order status management
  * Admin dashboard



# 🧰 Tech Stack
## Backend
  * FastAPI
  * Async Python
  * SQLAlchemy 2.0 Async ORM
  * Alembic
  * Pydantic v2
  * asyncpg
  * JWT Authentication
  * Redis
  * httpx

## Telegram Bot
  * aiogram v3
  * FSM
  * Routers
  * Inline keyboards
  * CallbackData

## Frontend
  * React
  * TypeScript
  * Vite

## Infrastructure
  * Docker
  * Docker Compose
  * PostgreSQL
  * Redis



# 🏗 Architecture

Telegram Bot / React Frontend   ->   FastAPI Backend ->   PostgreSQL / Redis



# ⚡ Async Architecture

Project uses fully asynchronous architecture:

* FastAPI async endpoints
* async SQLAlchemy
* aiogram
* asyncpg
* Redis async operations
* httpx async client

This allows the application to efficiently handle multiple concurrent I/O operations.



# 📦 Docker Services

| Service | Description         |
| ------- | ------------------- |
| backend | FastAPI backend     |
| bot     | Telegram bot        |
| db      | PostgreSQL          |
| redis   | Redis cache/storage |
| web     | React frontend      |



# 📁 Project Structure

* backend/     -> FastAPI backend
* bot/         -> Telegram bot
* web/         -> React frontend
* alembic/     -> database migrations
* media/       -> uploaded files



# 🔐 Authentication

 * JWT Access Tokens
 * Refresh Tokens
 * Refresh Token Rotation
 * Password hashing
 * Protected routes



# 🔥 Main Functionalities

 * REST API
 * Dockerized infrastructure
 * Telegram bot integration
 * Product image uploads
 * Pagination
 * Admin dashboard
 * Order lifecycle management
 * Redis caching



## Create `.env`

 * DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/shop
 * JWT_SECRET=supersecret
 * REDIS_URL=redis://redis:6379/0
 * BOT_TOKEN=your_bot_token



## Build & Run
docker compose up -d --build

## Apply migrations
docker compose exec backend alembic upgrade head



# 🌐 Access

## Backend API
http://localhost:8000/docs

## Frontend
http://localhost:5173
