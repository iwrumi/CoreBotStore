# Overview

This is a Telegram Store Bot application built with Flask and python-telegram-bot. The system provides an e-commerce platform where users can browse products, add items to cart, and place orders through a Telegram bot interface. It includes a web-based admin panel for managing products and orders, with data persistence handled through JSON files.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
The application follows a modular Flask architecture with clear separation of concerns:

- **Flask Web Application**: Serves as the admin interface and API layer, handling HTTP requests and rendering templates
- **Telegram Bot Integration**: Uses python-telegram-bot library to handle Telegram API interactions, bot commands, and conversation flows
- **Data Management Layer**: Custom DataManager class handles all data operations with JSON file persistence
- **Model Layer**: Object-oriented models (Product, Order, User) provide data structure and validation

## Frontend Architecture
- **Server-Side Rendering**: Flask templates using Jinja2 for dynamic content generation
- **Bootstrap Dark Theme**: Modern responsive UI with dark theme specifically designed for admin interfaces
- **Client-Side JavaScript**: Handles form submissions, AJAX requests, and dynamic UI updates
- **Font Awesome Icons**: Consistent iconography throughout the interface

## Data Storage Solution
The application uses a file-based JSON storage system instead of a traditional database:

- **Products Storage**: Products data stored in `data/products.json` with default sample data
- **Orders Storage**: Order information persisted in `data/orders.json`
- **Users Storage**: User data maintained in `data/users.json`
- **Session Management**: In-memory user sessions for bot interactions with cart and conversation state

This approach was chosen for simplicity and ease of deployment, avoiding database setup complexity while maintaining data persistence.

## Bot Architecture
- **Conversation Handler**: Implements state-based conversation flows for checkout process
- **Session Management**: Per-user session tracking for cart contents and navigation state
- **Command System**: Structured command handlers for different bot functionalities
- **Callback Query System**: Inline keyboard interactions for seamless user experience

## Security Considerations
- **Environment Variables**: Sensitive data like bot tokens stored as environment variables
- **Session Secrets**: Flask session management with configurable secret keys
- **Proxy Support**: ProxyFix middleware for proper header handling in deployment environments

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web framework for admin interface and API endpoints
- **python-telegram-bot**: Official Telegram Bot API wrapper for bot functionality
- **Werkzeug**: WSGI utilities including ProxyFix for deployment

## Frontend Dependencies
- **Bootstrap (CDN)**: UI framework with custom dark theme from Replit CDN
- **Font Awesome (CDN)**: Icon library for consistent interface elements
- **JavaScript**: Vanilla JavaScript for client-side interactions

## External Services
- **Telegram Bot API**: Primary integration for bot functionality requiring BOT_TOKEN
- **No Database**: System operates without external database dependencies
- **No Payment Processing**: Basic order management without integrated payment systems

## Environment Configuration
- **BOT_TOKEN**: Required environment variable for Telegram bot authentication
- **SESSION_SECRET**: Optional environment variable for Flask session security (defaults to development key)

The architecture prioritizes simplicity and rapid deployment while maintaining clean separation between the web interface and bot functionality. The JSON-based storage solution eliminates database setup requirements but may need migration to a proper database solution for production scaling.