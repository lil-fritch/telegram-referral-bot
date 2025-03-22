import sqlite3 as sql

def start_sql():
    global db, cur
    db = sql.connect('database.db')
    db.execute('PRAGMA foreign_keys = ON')
    cur = db.cursor()   
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS teams(
            unique_code TEXT PRIMARY KEY, 
            creator_id INTEGER, 
            name TEXT,
            reward INTEGER DEFAULT 0,
            min_count INTEGER DEFAULT 1,
            time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS user_languages(
            user_id INTEGER PRIMARY KEY,
            language_code TEXT
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS team_members(
            team_unique_code TEXT, 
            user_id INTEGER, 
            inviter_id INTEGER,
            role TEXT, 
            time_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (team_unique_code, user_id),
            FOREIGN KEY (team_unique_code) REFERENCES teams(unique_code),
            FOREIGN KEY (user_id) REFERENCES user_languages(user_id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS users_referrals(
            user_id INTEGER,
            team_unique_code TEXT,
            referral_count INTEGER,
            unsubscribed INTEGER,
            considered INTEGER,
            paid INTEGER,
            PRIMARY KEY (user_id, team_unique_code),
            FOREIGN KEY (user_id) REFERENCES user_languages(user_id)
        )
    ''')
 
    db.execute('''
        CREATE TABLE IF NOT EXISTS sponsors(
            team_unique_code TEXT, 
            link TEXT,
            channel_id INTEGER,
            PRIMARY KEY (team_unique_code, link),
            FOREIGN KEY (team_unique_code) REFERENCES teams(unique_code)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS allowed_team(
            user_id INTEGER, 
            allowed_teams INTEGER,
            created_teams INTEGER,
            PRIMARY KEY (user_id),
            FOREIGN KEY (user_id) REFERENCES user_languages(user_id)
        )
    ''')
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS application(
            user_id INTEGER, 
            team_unique_code INTEGER,
            username TEXT,
            amount INTEGER,
            reward INTEGER,
            count_referrals INTEGER,
            url TEXT,
            is_paid INTEGER DEFAULT 0,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            application_id INTEGER PRIMARY KEY AUTOINCREMENT,
            FOREIGN KEY (user_id) REFERENCES user_languages(user_id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS channels(
            channel_id INTEGER, 
            channel_name TEXT,
            PRIMARY KEY (channel_id)
        )
    ''')
    
    try:
        db.execute('ALTER TABLE allowed_team ADD COLUMN username TEXT')
    except:
        pass

    db.commit()
    
    return db, cur

async def set_user_referrals_count(user_id, team_unique_code, referral_count):  
    try:
        cur.execute('UPDATE users_referrals SET referral_count = ? WHERE user_id = ? AND team_unique_code = ?', (referral_count, user_id, team_unique_code))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_actual_user_referrals(user_id, team_unique_code):
    cur.execute('SELECT COUNT(*) FROM team_members WHERE inviter_id = ? AND team_unique_code = ?', (user_id, team_unique_code))
    return cur.fetchone()

async def add_count_in_db(user_id, team_unique_code, count):
    try:
        cur.execute('UPDATE users_referrals SET referral_count = referral_count + ? WHERE user_id = ? AND team_unique_code = ?', (count, user_id, team_unique_code))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def set_user_referrals_in_db(user_id, team_unique_code, referral_count, unsubscribed, considered, paid):
    try:
        cur.execute('UPDATE users_referrals SET referral_count = ?, unsubscribed = ?, considered = ?, paid = ? WHERE user_id = ? AND team_unique_code = ?', (referral_count, unsubscribed, considered, paid, user_id, team_unique_code))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_user_id_by_username(username):
    cur.execute('SELECT user_id FROM allowed_team WHERE username = ?', (username,))
    return cur.fetchone()

async def get_inviter_username(user_id):
    cur.execute('SELECT username FROM allowed_team WHERE user_id = ?', (user_id,))
    return cur.fetchone()

async def get_inviter_id(user_id, team_unique_code):
    if team_unique_code is None:
        team_unique_code = 'swag'
    cur.execute('SELECT inviter_id FROM team_members WHERE user_id = ? AND team_unique_code = ?', (user_id, team_unique_code))
    return cur.fetchone()


async def add_username(username, user_id):
    try:
        cur.execute('UPDATE allowed_team SET username = ? WHERE user_id = ?', (username, user_id))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    
def get_languages():
    cur.execute('SELECT * FROM user_languages')
    return cur.fetchall()

async def get_payments_by_username(username, team_unique_code):
    cur.execute('SELECT * FROM application WHERE username = ? AND team_unique_code = ?', (username, team_unique_code))
    return cur.fetchall()

async def remove_application(application_id):
    try:
        cur.execute('DELETE FROM application WHERE application_id = ?', (application_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_channels():
    cur.execute('SELECT * FROM channels')
    return cur.fetchall()

async def add_channel(channel_id, channel_name):
    try:
        cur.execute('INSERT INTO channels (channel_id, channel_name) VALUES (?, ?)', (channel_id, channel_name))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def update_min_count_referrals(team_unique_code, value):
    try:
        cur.execute('UPDATE teams SET min_count = ? WHERE unique_code = ?', (value, team_unique_code))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_applications(team_unique_code):
    cur.execute('SELECT * FROM application WHERE team_unique_code = ?', (team_unique_code,))
    return cur.fetchall()

async def add_application(user_id, team_unique_code, username, amount, reward, count_referrals, url):
    try:
        cur.execute('INSERT INTO application (user_id, team_unique_code, username, amount, reward, count_referrals, url) VALUES (?, ?, ?, ?, ?, ?, ?)', (user_id, team_unique_code, username, amount, reward, count_referrals, url))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def set_paid_application(application_id):
    try:
        cur.execute('UPDATE application SET is_paid = 1 WHERE application_id = ?', (application_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def is_allowed_team(user_id):
    cur.execute('SELECT CASE WHEN (allowed_teams - created_teams) > 0 THEN 1 ELSE 0 END AS can_create_more_teams FROM allowed_team WHERE user_id = ?', (user_id,))
    result = cur.fetchone()

    return bool(result[0])

async def update_admin(team_unique_code, user_id):
    try:
        cur.execute('UPDATE team_members SET role = ? WHERE user_id = ? AND team_unique_code = ?', ('admin', user_id, team_unique_code))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_admins(team_unique_code):
    cur.execute('SELECT user_id FROM team_members WHERE team_unique_code = ? AND role = ?', (team_unique_code, 'admin'))
    return cur.fetchall()

async def is_team_member(user_id, team_unique_code):
    cur.execute('SELECT 1 FROM team_members WHERE user_id = ? AND team_unique_code = ?', (user_id, team_unique_code))
    return bool(cur.fetchone())

async def get_team_members(team_unique_code):
    cur.execute('SELECT user_id FROM team_members WHERE team_unique_code = ?', (team_unique_code,))
    return cur.fetchall()

async def add_allow_team_in_db(user_id):
    try:
        cur.execute('UPDATE allowed_team SET allowed_teams = allowed_teams + 1 WHERE user_id = ?', (user_id,))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def create_allowed_team(user_id, username):
    try:
        cur.execute('INSERT INTO allowed_team (user_id, allowed_teams, created_teams, username) VALUES (?, ?, ?, ?)', (user_id, 0, 0, username))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_user_referrals(user_id, team_unique_code):
    cur.execute('SELECT user_id FROM team_members WHERE inviter_id = ? AND team_unique_code = ?', (user_id, team_unique_code))
    return cur.fetchall()

async def add_paid(user_id, team_unique_code, value):
    try:
        cur.execute('UPDATE users_referrals SET paid = paid + ? WHERE user_id = ? AND team_unique_code = ?', (value, user_id, team_unique_code))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def set_paid(user_id, value):
    try:
        cur.execute('UPDATE users_referrals SET paid = ? WHERE user_id = ?', (value, user_id))
        db.commit()
    except Exception as e:
        print(f"Error: {e}")

async def get_paid(user_id, team_unique_code):
    cur.execute('SELECT paid FROM users_referrals WHERE user_id = ? AND team_unique_code = ?', (user_id, team_unique_code))
    return cur.fetchone()

async def set_referral(user_id, team_unique_code):
    try:
        cur.execute('INSERT INTO users_referrals (user_id, team_unique_code, referral_count, unsubscribed, considered, paid) VALUES (?, ?, ?, ?, ?, ?)', (user_id, team_unique_code, 0, 0, 0, 0))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def set_unsubscribed(user_id, team_unique_code, value):
    try:
        cur.execute('UPDATE users_referrals SET unsubscribed = ? WHERE user_id = ? AND team_unique_code = ?', (value, user_id, team_unique_code))
        db.commit()
    except Exception as e:
        print(f"Error: {e}")

async def remove_considered(user_id, team_unique_code, value):
    try:
        cur.execute('UPDATE users_referrals SET considered = considered - ? WHERE user_id = ? AND team_unique_code = ?', (value, user_id, team_unique_code))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_all_users(team_unique_code):
    cur.execute('SELECT user_id FROM team_members WHERE team_unique_code = ?', (team_unique_code,))
    return cur.fetchall()

async def add_considered(user_id, team_unique_code, value):
    try:
        cur.execute('UPDATE users_referrals SET considered = considered + ? WHERE user_id = ? AND team_unique_code = ?', (value, user_id, team_unique_code))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_considered(user_id, team_unique_code):
    cur.execute('SELECT considered FROM users_referrals WHERE user_id = ? AND team_unique_code = ?', (user_id, team_unique_code))
    return cur.fetchone()

async def get_unsubscribed(user_id, team_unique_code):
    cur.execute('SELECT unsubscribed FROM users_referrals WHERE user_id = ? AND team_unique_code = ?', (user_id, team_unique_code))
    return cur.fetchone()

async def add_referral(user_id):
    try:
        cur.execute('UPDATE users_referrals SET referral_count = referral_count + 1 WHERE user_id = ?', (user_id,))
        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        
async def get_user_referrals_count(user_id, team_unique_code):
    cur.execute('SELECT referral_count FROM users_referrals WHERE user_id = ? AND team_unique_code = ?', (user_id, team_unique_code))
    return cur.fetchone()

async def update_reward(team_unique_code, reward):
    try:
        cur.execute('UPDATE teams SET reward = ? WHERE unique_code = ?', (reward, team_unique_code))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_min_count_referrals(team_unique_code):
    cur.execute('SELECT min_count FROM teams WHERE unique_code = ?', (team_unique_code,))
    return cur.fetchone()

async def get_reward(team_unique_code):
    cur.execute('SELECT reward FROM teams WHERE unique_code = ?', (team_unique_code,))
    return cur.fetchone()

async def get_team_name(team_unique_code):
    try:
        cur.execute('SELECT name FROM teams WHERE unique_code = ?', (team_unique_code,))
        return cur.fetchone()[0]
    except Exception as e:
        print(f"Error: {e}")
        return None

async def remove_admin_from_db(team_unique_code, user_id):
    try:
        cur.execute('UPDATE team_members SET role = ? WHERE user_id = ? AND team_unique_code = ?', ('user', user_id, team_unique_code))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def remove_sponsor_from_db(team_unique_code, link):
    try:
        cur.execute('DELETE FROM sponsors WHERE team_unique_code = ? AND link = ?', (team_unique_code, link))
        if cur.rowcount == 0:
            return False
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_sponsors_ids(team_unique_code):
    cur.execute('SELECT channel_id FROM sponsors WHERE team_unique_code = ?', (team_unique_code,))
    return cur.fetchall()

async def get_team_sponsors(team_unique_code):
    cur.execute('SELECT link FROM sponsors WHERE team_unique_code = ?', (team_unique_code,))
    return cur.fetchall()   

async def add_sponsor_in_db(team_unique_code, link, channel_id):
    try:
        cur.execute('INSERT INTO sponsors (team_unique_code, link, channel_id) VALUES (?, ?, ?)', (team_unique_code, link, channel_id))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_user_role(user_id, team_unique_code):
    cur.execute('SELECT role FROM team_members WHERE user_id = ? AND team_unique_code = ?', (user_id, team_unique_code))
    return cur.fetchone()[0]

async def get_team_unique_code_by_name(name):
    cur.execute('SELECT unique_code FROM teams WHERE name = ?', (name,))
    return cur.fetchone()

async def get_user_team_names(user_id):
    cur.execute('''
        SELECT teams.name
        FROM teams
        JOIN team_members ON teams.unique_code = team_members.team_unique_code
        WHERE team_members.user_id = ?
    ''', (user_id,))
    
    teams = cur.fetchall()
    return [team[0] for team in teams]

async def add_team_member(team_unique_code, user_id, role, inviter_id=None):
    try:
        cur.execute('INSERT INTO team_members (team_unique_code, user_id, inviter_id, role) VALUES (?, ?, ?, ?)', (team_unique_code, user_id, inviter_id, role))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def set_language(user_id, language_code):
    try:
        cur.execute('INSERT OR REPLACE INTO user_languages (user_id, language_code) VALUES (?, ?)', (user_id, language_code))
        db.commit()
    except Exception as e:
        print(f"Error: {e}")

async def get_user_time_joined(user_id, team_unique_code):
    cur.execute('SELECT time_joined FROM team_members WHERE user_id = ? AND team_unique_code = ?', (user_id, team_unique_code))
    return cur.fetchone()

async def get_user_language(user_id):
    cur.execute('SELECT language_code FROM user_languages WHERE user_id = ?', (user_id,))
    return cur.fetchone()

async def get_team_by_unique_code(unique_code):
    cur.execute('SELECT * FROM teams WHERE unique_code = ?', (unique_code,))
    return cur.fetchone()

async def add_created_team(user_id):
    try:
        cur.execute('UPDATE allowed_team SET created_teams = created_teams + 1 WHERE user_id = ?', (user_id,))
        db.commit()
    except Exception as e:
        print(f"Error: {e}")

async def create_team_in_db(unique_code, creator_id, name):
    try:
        cur.execute('INSERT INTO teams (unique_code, creator_id, name) VALUES (?, ?, ?)', (unique_code, creator_id, name))
        db.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False