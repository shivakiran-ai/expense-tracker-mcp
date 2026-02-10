# 🏦 Expense Tracker - AI-Powered Personal Finance Assistant

An intelligent expense tracking system powered by Claude AI using the MCP (Model Context Protocol) framework.

## 📋 Project Overview

This is a 16-day learning project to build a production-ready expense tracker with AI capabilities.

### ✨ Features (In Progress)

- 💬 Natural language expense input via AI chatbot
- 💱 Multi-currency support (10+ currencies)
- 📊 Smart categorization with predefined categories
- 💳 Payment method tracking
- 📈 Analytics and insights
- 💰 Budget management

## 🏗️ Architecture
```
Traditional User Signup → AI-Powered Expense Tracking
```

- **User Profile Creation**: Traditional (no LLM)
- **Expense Management**: AI chatbot using FastMCP
- **Data Storage**: MongoDB with async operations
- **Currency**: Store in USD, preserve original amounts

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastMCP** - MCP framework
- **Motor** - Async MongoDB driver
- **Pydantic v2** - Data validation
- **Claude AI** - Natural language processing

## 📁 Project Structure
```
expense-tracker/
├── src/
│   └── expense_server/
│       ├── database/
│       │   ├── connection.py    # Database layer
│       │   └── models.py        # Pydantic models
│       └── utils/
│           └── currency.py      # Currency conversion
├── .env                         # Environment variables
├── pyproject.toml               # Dependencies
└── README.md
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.11 or higher
- MongoDB (local or Atlas)
- uv package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/expense-tracker-mcp.git
cd expense-tracker-mcp
```

2. Install dependencies:
```bash
uv sync
```

3. Create `.env` file:
```bash
MONGODB_URI=mongodb://localhost:27017
```

4. Run tests:
```bash
uv run python test_models.py
uv run python test_currency.py
```

## 📚 Progress

### Day 1: Foundation ✅
- [x] Database connection with Singleton pattern
- [x] Complete Pydantic models with validation
- [x] Multi-currency support with API integration
- [x] Predefined categories and payment methods
- [x] Helper functions and validators

### Day 2: MCP Tools (In Progress)
- [ ] Build add_expense tool
- [ ] Build get_expenses tool
- [ ] Build delete_expense tool
- [ ] Test with Claude chatbot

### Days 3-16: Coming Soon
- Analytics
- Budgets
- User management
- Advanced features

## 🎓 Learning Journey

This project is part of a structured 16-day learning program focusing on:
- Async Python programming
- MCP protocol integration
- FastMCP framework
- Pydantic validation
- MongoDB operations
- Production-ready architecture

## 📝 License

This project is for educational purposes.

## 🙏 Acknowledgments

- Built with guidance from Claude AI
- Uses FastMCP framework by Anthropic
- Currency data from ExchangeRate-API

---

**Status**: Day 1 Complete ✅ | In Active Development 🚧