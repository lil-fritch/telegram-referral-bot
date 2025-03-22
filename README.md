# Telegram Referral Bot 💸

## 📌 Description
A Telegram bot with a referral system and payout requests, built for traffic arbitrage and user acquisition tasks. Features an admin panel for user management and payout approvals. Built with Aiogram and SQLite3.

## 🚀 Features
- Referral system with unique invite links
- Automatic reward tracking for user invites
- Admin panel to manage users, settings, and payout requests
- Custom async functions for efficient user interaction and database operations
- Raw SQL queries for optimized database control
- SQLite3 as the main database
- Successfully served 35,000+ users over 6 months

## 🛠 Tech Stack
- Python
- Aiogram
- SQLite3
- AsyncIO

## 🔧 Installation
1. Clone the repo  
```bash
git clone https://github.com/lil-fritch/telegram-referral-bot.git
cd telegram-referral-bot
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Add your Telegram ID to the list and replace the bot token (create_bot.py)
```python
ADMINS = [

]

ALLOWED_USERS = [

]

bot = Bot('TOKEN')
```
4. Run the bot
```bash
python start_bot.py
```
## 📫 Contact
For questions: fritch.high@gmail.com
