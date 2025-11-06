# Foodie - Food Ordering Application

Foodie is a full-stack food ordering application with comprehensive Role-Based Access Control (RBAC) and relational access model that restricts users to data from their assigned country.

## Features

### Access Control

The application implements a comprehensive RBAC system with three roles:

| Function                      | ADMIN            | MANAGER        | MEMBER         |
| ----------------------------- | ---------------- | -------------- | -------------- |
| View restaurants & menu items | ✅ All countries | ✅ Own country | ✅ Own country |
| Create order (add food items) | ✅               | ✅             | ✅             |
| Place order (checkout & pay)  | ✅               | ✅             | ❌             |
| Cancel order                  | ✅               | ✅             | ❌             |
| Update payment method         | ✅               | ❌             | ❌             |

### Bonus: Relational Access Model

- **ADMIN**: Can access data from all countries
- **MANAGER & MEMBER**: Can only view and act on data from their assigned country
- Example: A Manager in India cannot access restaurants, orders, or data from America

## Technology Stack

- **Backend**: Flask 3.1+ (Python 3.12+)
- **ORM**: SQLAlchemy 2.0+ for database operations
- **Database**: SQLite
- **Frontend**: Jinja2 templates with Bootstrap
- **Authentication**: Session-based with werkzeug password hashing
- **Package Management**: uv

## Installation & Setup

### Prerequisites

- Python 3.12 or higher
- [uv package manager](https://docs.astral.sh/uv/getting-started/installation/)

### Installation Steps

1. **Clone the repository**

```bash
git clone <repository-url>
cd slooze-fullstack-challenge
```

2. **Install dependencies**

```bash
uv sync
```

4. **Seed the database with test data**

```bash
uv run flask --app foodie seed-db
```

5. **Run the application**

```bash
uv run flask --app foodie run
```

6. **Access the application**
   Open your browser and navigate to: `http://127.0.0.1:5000`

## Test Accounts

All test accounts use the password: `password123`

| Username        | Password    | Role    | Country | Description                     |
| --------------- | ----------- | ------- | ------- | ------------------------------- |
| nick.fury       | password123 | ADMIN   | America | Business owner with full access |
| captain.marvel  | password123 | MANAGER | India   | Manager for India operations    |
| captain.america | password123 | MANAGER | America | Manager for America operations  |
| thanos          | password123 | MEMBER  | India   | Team member in India            |
| thor            | password123 | MEMBER  | India   | Team member in India            |
| travis          | password123 | MEMBER  | America | Team member in America          |

## API Routes

### Authentication

- `GET/POST /auth/login` - User login
- `GET /auth/logout` - User logout

### Restaurants

- `GET /restaurants/` - List all accessible restaurants
- `GET /restaurants/<id>` - View restaurant details and menu

### Orders

- `GET /orders/` - List user's orders
- `GET /orders/<id>` - View order details
- `POST /orders/create/<restaurant_id>` - Create new draft order
- `GET /orders/<id>/edit` - Edit draft order (shopping cart)
- `POST /orders/<id>/add-item` - Add item to order
- `POST /orders/<id>/remove-item/<item_id>` - Remove item from order
- `GET/POST /orders/<id>/place` - Checkout and place order (ADMIN/MANAGER only)
- `POST /orders/<id>/cancel` - Cancel order (ADMIN/MANAGER only)
- `POST /orders/<id>/update-payment` - Update payment method (ADMIN only)

### Admin

- `GET /admin/` - Admin dashboard
- `GET /admin/payment-methods` - List payment methods
- `GET/POST /admin/payment-methods/add` - Add payment method
- `GET/POST /admin/payment-methods/<id>/edit` - Edit payment method
- `POST /admin/payment-methods/<id>/toggle` - Toggle payment method status

## Development

### Run in Development Mode

```bash
uv run flask --app foodie run --debug
```

### Reset Database

```bash
rm instance/foodie.sqlite
uv run flask --app foodie seed-db
```

## Docker Deployment

```bash
docker-compose up -d
```

### Environment Variables

- `SECRET_KEY` - Flask secret key for session management (default: "dev")
- `FLASK_ENV` - Flask environment (default: production in Docker)

## Future Enhancements

- Register user functionality
- Add more granular roles
  - Store manager can only look at their restaurant
  - Regional managers can look at all restaurants in the region
- Improve frontend
  - Static, serverside right now, needs to be dynamic
  - Cache cart orders in the frontend to reduce API requests
    - Maybe only commit to database when they go through the checkout section
- Menu Items is available property
- Concurrent orders for the same resturant
- Customer name in order
