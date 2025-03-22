from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from translations import get_translation

from database.sql import get_user_team_names, get_channels


async def all_channels_kb(message):
    all_channels = await get_channels()
    all_channels_kb = InlineKeyboardMarkup(row_width=2)
    
    for channel in all_channels:
        channel_btn = InlineKeyboardButton(text=channel[1], callback_data=f'channel:{channel[0]}')
        all_channels_kb.insert(channel_btn)
    
    back_text = await get_translation(message, 'back_btn')
    add_temp_text = await get_translation(message, 'add_temp_btn')
    
    back_btn = InlineKeyboardButton(text=back_text, callback_data='teamstart')
    add_temp_btn = InlineKeyboardButton(text=add_temp_text, callback_data='channel:add_temp')
    
    all_channels_kb.row(add_temp_btn)
    all_channels_kb.row(back_btn)
    
    return all_channels_kb

async def get_start_kb(message):
    start_kb = InlineKeyboardMarkup(row_width=2)

    team_names = await get_user_team_names(message.from_user.id)   
    for team_name in team_names:
        team_name_btn = InlineKeyboardButton(text=f'«{team_name}»', callback_data=f'team_{team_name}')
        start_kb.insert(team_name_btn) 
        
    change_language_text = await get_translation(message, 'change_language_btn')
    create_team_text = await get_translation(message, 'create_team_btn')
    admin_text = await get_translation(message, 'admin_btn')
    
    change_language_btn = InlineKeyboardButton(text=change_language_text, callback_data='change_language')
    create_team_btn = InlineKeyboardButton(text=create_team_text, callback_data='create_team')
    admin_btn = InlineKeyboardButton(text=admin_text, url='https://t.me/yallii666')
    
    start_kb.add(create_team_btn, change_language_btn).row(admin_btn)
    return start_kb

async def get_confirmation_kb(message):
    confirmation_kb = InlineKeyboardMarkup()
    
    yes_text = await get_translation(message, 'yes_btn')
    no_text = await get_translation(message, 'no_btn')
    
    yes_btn = InlineKeyboardButton(text=yes_text, callback_data='yes')
    no_btn = InlineKeyboardButton(text=no_text, callback_data='no')
    
    confirmation_kb.add(yes_btn, no_btn)
    
    return confirmation_kb

async def admin_kb(message):
    admin_kb = InlineKeyboardMarkup(row_width=2)
    
    admin_text = await get_translation(message, 'admin_btn')
    back_text = await get_translation(message, 'start_btn')

    admin_btn = InlineKeyboardButton(text=admin_text, url='https://t.me/yallii666')
    back_btn = InlineKeyboardButton(text=back_text, callback_data='start')
    
    admin_kb.add(admin_btn).add(back_btn)

    return admin_kb

async def fake_check(message):
    go_to_start_kb = InlineKeyboardMarkup()
    
    start_text = await get_translation(message, 'check_sub_btn')
    start_btn = InlineKeyboardButton(text=start_text, callback_data='fake_check_sub')
    
    go_to_start_kb.add(start_btn)
    
    return go_to_start_kb

async def go_to_start_kb(message):
    go_to_start_kb = InlineKeyboardMarkup()
    
    start_text = await get_translation(message, 'start_btn')
    start_btn = InlineKeyboardButton(text=start_text, callback_data='start')
    
    go_to_start_kb.add(start_btn)
    
    return go_to_start_kb

async def team_start_kb_general(message):
    team_start_kb = InlineKeyboardMarkup(row_width=2)
    
    my_stats_text = await get_translation(message, 'my_stats_btn')
    get_link_text = await get_translation(message, 'get_link_btn')
    submit_application = await get_translation(message, 'submit_application_btn')
    
    my_stats_btn = InlineKeyboardButton(text=my_stats_text, callback_data=f'my_stats')
    get_link_btn = InlineKeyboardButton(text=get_link_text, callback_data=f'get_link')
    submit_application_btn = InlineKeyboardButton(text=submit_application, callback_data='submit_application')
    
    
    team_start_kb.add(my_stats_btn, get_link_btn)
    team_start_kb.row(submit_application_btn)
    
    return team_start_kb

async def team_start_kb_user(message):
    team_start_kb = await team_start_kb_general(message)    
    
    back_text = await get_translation(message, 'back_btn')
    
    back_btn = InlineKeyboardButton(text=back_text, callback_data='back')
    
    team_start_kb.row(back_btn)
    
    return team_start_kb

async def team_start_kb_creator(message):
    team_start_kb = await team_start_kb_general(message)
    
    management_text = await get_translation(message, 'management_btn')
    back_text = await get_translation(message, 'back_btn')
    global_statistic_text = await get_translation(message, 'global_statistic_btn')
    payments_text = await get_translation(message, 'payments_btn')
    paid_payments_text = await get_translation(message, 'payed_payments_btn')

    management_btn = InlineKeyboardButton(text=management_text, callback_data='management')
    back_btn = InlineKeyboardButton(text=back_text, callback_data='back')
    global_statistic_btn = InlineKeyboardButton(text=global_statistic_text, callback_data='global_statistic')
    payments_btn = InlineKeyboardButton(text=payments_text, callback_data='payments')
    paid_payments_btn = InlineKeyboardButton(text=paid_payments_text, callback_data='paid_payments')
    
    team_start_kb.add(global_statistic_btn).insert(management_btn).insert(payments_btn).insert(paid_payments_btn)
    team_start_kb.row(back_btn)
    
    return team_start_kb

async def team_start_kb_managment(message):
    managment_kb = InlineKeyboardMarkup(row_width=2)
    
    add_sponsor_text = await get_translation(message, 'add_sponsor_btn')
    remove_sponsor_text = await get_translation(message, 'remove_sponsor_btn')
    add_admin_text = await get_translation(message, 'add_admin_btn')
    remove_admin_text = await get_translation(message, 'remove_admin_btn')
    back_text = await get_translation(message, 'back_btn')
    set_reward_text = await get_translation(message, 'set_reward_btn')
    set_min_count = await get_translation(message, 'set_min_count_btn')

    add_sponsor_btn = InlineKeyboardButton(text=add_sponsor_text, callback_data='add_sponsor')
    remove_sponsor_btn = InlineKeyboardButton(text=remove_sponsor_text, callback_data='remove_sponsor')
    add_admin_btn = InlineKeyboardButton(text=add_admin_text, callback_data='add_admin')
    remove_admin_btn = InlineKeyboardButton(text=remove_admin_text, callback_data='remove_admin')
    set_reward_btn = InlineKeyboardButton(text=set_reward_text, callback_data='set_reward')
    set_min_count_btn = InlineKeyboardButton(text=set_min_count, callback_data='set_min_count')
    
    back_btn = InlineKeyboardButton(text=back_text, callback_data='teamstart')
    
    managment_kb.insert(add_sponsor_btn).insert(remove_sponsor_btn)
    managment_kb.insert(add_admin_btn).insert(remove_admin_btn)
    managment_kb.insert(set_reward_btn).insert(set_min_count_btn)
    managment_kb.row(back_btn)
    
    return managment_kb
    
async def team_start_kb_admin(message):
    team_start_kb = await team_start_kb_general(message)
    
    payments_text = await get_translation(message, 'payments_btn')
    paid_payments_text = await get_translation(message, 'payed_payments_btn')
    
    payments_btn = InlineKeyboardButton(text=payments_text, callback_data='payments')
    paid_payments_btn = InlineKeyboardButton(text=paid_payments_text, callback_data='paid_payments')
    
    team_start_kb.add(payments_btn).insert(paid_payments_btn)
    
    back_text = await get_translation(message, 'start_team_btn')
    back_btn = InlineKeyboardButton(text=back_text, callback_data='teamstart')
    team_start_kb.row(back_btn)
    
    return team_start_kb
    
async def go_to_start_team_kb(message):
    go_to_start_team_kb = InlineKeyboardMarkup()
    
    start_text = await get_translation(message, 'start_team_btn')
    start_btn = InlineKeyboardButton(text=start_text, callback_data='teamstart')
    
    go_to_start_team_kb.add(start_btn)
    return go_to_start_team_kb

async def get_sponsors_kb(message, sponsors):
    sponsors_kb = InlineKeyboardMarkup()
    
    for sponsor in sponsors:
        sponsor_btn = InlineKeyboardButton(text=sponsor[0], callback_data='sponsor_' + sponsor[0])
        sponsors_kb.add(sponsor_btn)
    back_text = await get_translation(message, 'start_team_btn')
    back_btn = InlineKeyboardButton(text=back_text, callback_data='teamstart')
    sponsors_kb.row(back_btn)
    return sponsors_kb

async def get_admins_kb(message, admins):
    admins_kb = InlineKeyboardMarkup()
    
    for admin in admins:
        print('admin_'+str(admin[0]))
        admin_btn = InlineKeyboardButton(text=admin[0], callback_data='admin_' + str(admin[0]))
        admins_kb.add(admin_btn)
    back_text = await get_translation(message, 'start_team_btn')
    back_btn = InlineKeyboardButton(text=back_text, callback_data='teamstart')
    admins_kb.row(back_btn)
    return admins_kb

async def sponsorship_kb(message, sponsors):
    sponsorship_kb = InlineKeyboardMarkup(row_width=1)
    
    for sponsor in sponsors:
        sponsor_btn = InlineKeyboardButton(text=sponsor[0], url=sponsor[0])
        sponsorship_kb.add(sponsor_btn)
    
    return sponsorship_kb

async def check_sub_kb(message):
    check_sub_kb = InlineKeyboardMarkup()
    
    check_text = await get_translation(message, 'check_sub_btn')
    
    check_btn = InlineKeyboardButton(text=check_text, callback_data='check_sub')
    
    check_sub_kb.add(check_btn)
    
    return check_sub_kb

async def my_stats_kb(message):
    my_stats_kb = await go_to_start_team_kb(message)
    
    update_text = await get_translation(message, 'update_stats_btn')
    
    update_btn = InlineKeyboardButton(text=update_text, callback_data='update_stats')
    
    my_stats_kb.row(update_btn)
    return my_stats_kb  

def get_payment_provider_kb():
    payment_provider_kb = InlineKeyboardMarkup()
    
    provider_1_text = 'Tranzzo (UA)'
    
    
    payment_provider_kb.add(provider_1_text)
    
    return payment_provider_kb

async def cancel_kb(message):
    cancel_kb = InlineKeyboardMarkup()
    
    back_text = await get_translation(message, 'back_btn')
    
    back_btn = InlineKeyboardButton(text=back_text, callback_data='back')
    
    cancel_kb.add(back_btn)
    
    return cancel_kb

async def choose_filter(message):
    choose_filter_kb = InlineKeyboardMarkup(row_width=2)
    
    all_text = await get_translation(message, 'all_btn')
    by_id_text = await get_translation(message, 'by_id_btn')
    by_username_text = await get_translation(message, 'by_username_btn')
    back_text = await get_translation(message, 'back_btn')

    
    all_btn = InlineKeyboardButton(text=all_text, callback_data='all')
    by_id_btn = InlineKeyboardButton(text=by_id_text, callback_data='by_id')
    by_username_btn = InlineKeyboardButton(text=by_username_text, callback_data='by_username')
    back_btn = InlineKeyboardButton(text=back_text, callback_data='teamstart')
        
    choose_filter_kb.row(all_btn)
    choose_filter_kb.row(by_id_btn).insert(by_username_btn)
    choose_filter_kb.add(back_btn)
    return choose_filter_kb

async def paid_choose_filter(message):
    choose_filter_kb = InlineKeyboardMarkup(row_width=2)
    
    all_text = await get_translation(message, 'all_btn')
    by_id_text = await get_translation(message, 'by_id_btn')
    by_username_text = await get_translation(message, 'by_username_btn')
    back_text = await get_translation(message, 'back_btn')

    
    all_btn = InlineKeyboardButton(text=all_text, callback_data='all_paid')
    by_id_btn = InlineKeyboardButton(text=by_id_text, callback_data='by_id_paid')
    by_username_btn = InlineKeyboardButton(text=by_username_text, callback_data='by_username_paid')
    back_btn = InlineKeyboardButton(text=back_text, callback_data='teamstart')
        
    choose_filter_kb.row(all_btn)
    choose_filter_kb.row(by_id_btn).insert(by_username_btn)
    choose_filter_kb.add(back_btn)
    return choose_filter_kb    

async def application_management(message, application_id, user_id, team_code, count):
    application_management_kb = InlineKeyboardMarkup(row_width=2)
    
    paid_text = await get_translation(message, 'paid_btn')
    delete_text = await get_translation(message, 'delete_btn')
    
    paid_btn = InlineKeyboardButton(text=paid_text, callback_data=f'paid:{application_id}:{user_id}:{team_code}:{count}')
    delete_btn = InlineKeyboardButton(text=delete_text, callback_data=f'delete:{application_id}')
    
    application_management_kb.insert(paid_btn).insert(delete_btn)
    return application_management_kb
    