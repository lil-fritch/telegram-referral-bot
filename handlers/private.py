from create_bot import bot, dp, ALLOWED_USERS as AL
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import filters
from database.sql import *
from keyboars.kb_private import *
from aiogram.types import ChatMemberStatus
from aiogram.utils.exceptions import ChatNotFound
from aiogram.types import ContentType 
import time
import requests
import math
from decimal import Decimal, getcontext

import re

from translations import get_translation as gt, choose_language, set_user_language

from aiocryptopay import AioCryptoPay, Networks

async def message_or_callback_handler(message_or_callback: types.Message | types.CallbackQuery):
    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.delete()
        message = message_or_callback.message
        message.from_user.id = message_or_callback.from_user.id
    else:
        message = message_or_callback
    return message

async def start(message_or_callback: types.Message | types.CallbackQuery):
    message = await message_or_callback_handler(message_or_callback)
    if message.chat.type == 'private':
        if await get_user_language(message.chat.id) == None:
            user_language = (message.from_user.language_code if message.from_user.language_code in ['uk', 'ru'] else 'ru')
            await set_language(message.from_user.id, user_language)
            await set_user_language(message.from_user.id, user_language)
            await create_allowed_team(message.from_user.id, message.from_user.username)         
        args = message.get_args()
        if args:
            await referral_handler(message, args)
            return
        else:
            if message.from_user.username != 'arbitration_assistantbot':
                await add_username(message.from_user.username, message.from_user.id)
            start_kb = await get_start_kb(message)
            await message.answer(str(await gt(message, 'start_message')).format(id=message.chat.id), reply_markup=start_kb, parse_mode='Markdown')

async def referral_handler(message: types.Message, args: str):
    if message.chat.type == 'private':
        args = args.split('-')
        team_unique_code = args[0]
        inviter_id = args[1]
        team_name = await get_team_name(team_unique_code)
        if not team_name:
            await message.answer(await gt(message, 'unknown team'), reply_markup=await go_to_start_kb(message))
            return
        sponsors = await get_team_sponsors(team_unique_code)
        sponsors = ['\n*'+sponsor[0]+'*' for sponsor in sponsors if sponsor[0] != 'https://t.me/swagtraffic']
        sponsors = ''.join(sponsors)
        text = str(await gt(message, 'team_chat'))
        sponsors = sponsors + '\n\n' + f'[{text}](https://t.me/swagtraffic)' + '\n' 
        user_team_data[message.from_user.id] = {
            'team_name': team_name,
            'team_unique_code': team_unique_code,
            'role': 'user',
            'inviter_id': inviter_id
        }
        if sponsors:
            await message.answer(str(await gt(message, 'referral_message')).format(team_name=team_name, sponsors=sponsors), reply_markup=await check_sub_kb(message), parse_mode='Markdown', disable_web_page_preview=True)
        else:
            await adding_user(message, team_unique_code, inviter_id)

async def check_sub(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
        inviter_id = user_team_data[callback.from_user.id]['inviter_id']
        sponsors = await get_team_sponsors(team_unique_code)
        sub_on_sponsors = await check_sponsor_subscription(callback, callback.from_user.id)
        if isinstance(sub_on_sponsors, bool) and sub_on_sponsors:
            await callback.message.delete()
            await adding_user(callback.message, team_unique_code, inviter_id)
        else:
            await callback.answer(str(await gt(callback.message, 'not_subscribed')).format(act=str(sub_on_sponsors), all=str(len(sponsors)))) 

async def fake_check_sub(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        allow = user_team_data[callback.from_user.id]['allow']
        if not allow:
            await callback.answer('Вы не подписались на спонсора!')
            user_team_data[callback.from_user.id]['allow'] = True
        else:
            user_team_data[callback.from_user.id]['allow'] = False
            await callback.message.delete()
            await team_start(callback)
    
async def is_bot_in_channel(channel_id):
    bot_info = await bot.get_me()
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=bot_info.id)
        return bool(member)
    except:
        return False        

async def adding_user(message: types.Message, team_unique_code: str, inviter_id: int):
    team_name = await get_team_name(team_unique_code)
    success = await add_team_member(team_unique_code, message.chat.id, 'user', inviter_id)
    if success:
        await set_referral(message.chat.id, team_unique_code)
        await message.answer(str(await gt(message, 'referral_success_message')).format(team_name=team_name), parse_mode='Markdown', reply_markup=await go_to_start_kb(message))
        await add_referral(inviter_id)
        
        original_language = (await get_user_language(message.chat.id))[0]
        inviter_language = (await get_user_language(inviter_id))[0]
        
        await set_user_language(message.chat.id, inviter_language)
        await bot.send_message(inviter_id, str(await gt(message, 'referral_joined_message')).format(team_name=team_name), parse_mode='Markdown')
        await set_user_language(message.chat.id, original_language)
        
    else:
        await message.answer(str(await gt(message, 'referral_error_message')).format(team_name=team_name), parse_mode='Markdown', reply_markup=await go_to_start_kb(message))


async def create_team(message_or_callback: types.Message | types.CallbackQuery):
    message = await message_or_callback_handler(message_or_callback)
    if message.chat.type == 'private':
        if await is_allowed_team(message.from_user.id):
            await CreateTeam.team_name.set()
            await message.answer(await gt(message, 'team_name_message'), reply_markup=await cancel_kb(message))
        else:
            await message.answer(await gt(message, 'not_allowed_team_message'), reply_markup=await admin_kb(message))
         
async def process_team_name(message: types.Message, state: FSMContext):
    if (
        await validate_team_name_length(message) and
        await validate_team_name_characters(message)
    ):
        await state.update_data(team_name=message.text)
        await CreateTeam.team_unique_code.set()
        await message.answer(await gt(message, 'team_unique_code_message'), reply_markup=await cancel_kb(message))
    
async def validate_team_name_length(message):
    if len(message.text) < 3 or len(message.text) > 20:
        await message.answer(await gt(message, 'team_name_length_error'))
        await CreateTeam.team_name.set()
    else: return True  

async def validate_team_name_characters(message):
    pattern = r'^[a-zA-Zа-яА-ЯёЁіїІЇґҐ0-9 ]+$'
    if not re.match(pattern, message.text):
        await message.answer(await gt(message, 'team_name_characters_error'))
        await CreateTeam.team_name.set()
    else:
        return True   

async def process_team_unique_code(message: types.Message, state: FSMContext):
    message.text = message.text.lower()
    if (
        await validate_team_unique_code_length(message) and
        await validate_team_unique_code_characters(message) and
        await validate_team_unique_code_uniqueness(message)
    ):
        await state.update_data(team_unique_code=message.text)
        data = await state.get_data()
        team_name = data.get('team_name')
        await message.answer(str(await gt(message, 'team_confirmation_message')).format(team_name=team_name, team_unique_code=message.text),\
            parse_mode='Markdown', \
            reply_markup=await get_confirmation_kb(message)
        )
        await CreateTeam.confirmation.set()
        
async def validate_team_unique_code_length(message):
    if len(message.text) != 4:
        await message.answer(await gt(message, 'team_unique_code_length_error'))
        await CreateTeam.team_unique_code.set()
    else: return True

async def validate_team_unique_code_characters(message):
    pattern = r'^[a-zA-Z]+$'
    if not re.match(pattern, message.text):
        await message.answer(await gt(message, 'team_unique_code_characters_error'))
        await CreateTeam.team_unique_code.set()
    else:
        return True

async def validate_team_unique_code_uniqueness(message):
    if await get_team_by_unique_code(message.text):
        await message.answer(await gt(message, 'team_unique_code_uniqueness_error'))
        await CreateTeam.team_unique_code.set()
    else:
        return True

async def process_team_confirmation(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'yes':
        
        data = await state.get_data()
        team_name = data.get('team_name')
        team_unique_code = data.get('team_unique_code')
        check_success1 = await create_team_in_db(team_unique_code, callback.from_user.id, team_name)
        check_success2 = await add_team_member(team_unique_code, callback.from_user.id, 'creator')
        check_success3 = await set_referral(callback.from_user.id, team_unique_code)
        check_success4 = await add_created_team(callback.from_user.id)
        await callback.message.delete()
        if check_success1 and check_success2 and check_success3:
            await callback.message.answer(await gt(callback.message, 'team_created_message'), reply_markup=await go_to_start_kb(callback.message))
        else:
            await callback.message.answer(await gt(callback.message, 'team_not_created_message'))
        await state.finish()
    else:
        await callback.answer(await gt(callback.message, 'cancelled_message'))
        await state.finish()
        await start(callback)
        return
    
    
class CreateTeam(StatesGroup):
    team_name = State()
    team_unique_code = State()
    confirmation = State()

user_team_data = {}

async def team_start(callback: types.CallbackQuery, buffer=1):
    if callback.message.chat.type == 'private':        
        team_name = callback.data.split('_')[1]
        team_unique_code = (await get_team_unique_code_by_name(team_name))[0]
        
        await callback.message.delete()
        reward = (await get_reward(team_unique_code))[0]
        min_count = (await get_min_count_referrals(team_unique_code))[0]

        count = (await get_user_referrals_count(callback.from_user.id, team_unique_code))[0]
        # unsubscribed = (await get_unsubscribed(callback.from_user.id, team_unique_code))[0]
        considered = (await get_considered(callback.from_user.id, team_unique_code))[0]
        paid = (await get_paid(callback.from_user.id, team_unique_code))[0]
        result = count - considered - paid
        
        role = await get_user_role(callback.from_user.id, team_unique_code)
        sponsors = ['\n*'+sponsor[0]+'*' for sponsor in (await get_team_sponsors(team_unique_code)) ]
        sponsors = ''.join(sponsors)
        
        admins = ['\n*'+str(admin[0])+'*' for admin in (await get_admins(team_unique_code))]
        admins = ''.join(admins)
                
        if sponsors == '':
            sponsors = await gt(callback.message, 'no_sponsors')
        if admins == '':
            admins = await gt(callback.message, 'no_admins')
            
        user_team_data[callback.from_user.id] = {
            'team_name': team_name,
            'team_unique_code': team_unique_code,
            'role': role,
            'reward': reward,
            'count': count,
            # 'unsubscribed': unsubscribed,
            'considered': considered,
            'paid': paid,
            'result': result,
            'allow': False
        }
        if role == 'creator':
            if buffer == 1:
                kb = await team_start_kb_creator(callback.message)
            else:
                kb = await team_start_kb_managment(callback.message)
            add_text = str(await gt(callback.message, 'add_text_pattern')).format(teamuniquecode=team_unique_code, team_name=team_name, sponsors=sponsors, admins=admins)
        elif role == 'admin':
            kb = await team_start_kb_admin(callback.message)
            add_text = str(await gt(callback.message, 'add_text_pattern')).format(teamuniquecode=team_unique_code, team_name=team_name, sponsors=sponsors, admins=admins)
        else:
            add_text = ''
            kb = await team_start_kb_user(callback.message)
        
        await callback.message.answer(str(await gt(callback.message, \
            'team_start_message')).format(team_name=team_name, 
            role=await gt(callback.message, role), id=callback.from_user.id, reward=reward, min_count=min_count, add_text=add_text), 
            parse_mode='Markdown', reply_markup=kb, disable_web_page_preview=True
        )

async def management(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        team_name = user_team_data[callback.from_user.id]['team_name']
        callback.data = 'team_' + team_name
        await team_start(callback, buffer=2)

async def global_statistic(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        await callback.message.answer(await gt(callback.message, 'temp'), reply_markup=await go_to_start_team_kb(callback.message))

async def submit_application(callback: types.CallbackQuery):
    # if callback.message.chat.type == 'private':
    #     await callback.answer(await gt(callback.message, 'temp'))
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        
        team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
        reward = user_team_data[callback.from_user.id]['reward']
        sponsors = await get_team_sponsors(team_unique_code)
        sponsors = ['\n'+sponsor[0] for sponsor in sponsors]
        sponsors = ''.join(sponsors)
        if reward == 0:
            await callback.message.answer(await gt(callback.message, 'reward_error_application'), reply_markup=await go_to_start_team_kb(callback.message))
            return
        sub_on_sponsors = await check_sponsor_subscription(callback, callback.from_user.id)
        if isinstance(sub_on_sponsors, bool) and sub_on_sponsors:
            
            count = (await get_user_referrals_count(callback.from_user.id, team_unique_code))[0]
            considered = (await get_considered(callback.from_user.id, team_unique_code))[0]
            paid = (await get_paid(callback.from_user.id, team_unique_code))[0]
            
            price = user_team_data[callback.from_user.id]['reward']
            
            # user_referrals = await get_user_referrals(callback.from_user.id, team_unique_code)
                            
            # unsubscribed = 0
            
            # for user_referral in user_referrals:
            #     sub_on_sponsors = await check_sponsor_subscription(callback, user_referral[0])
            #     if isinstance(sub_on_sponsors, bool) and sub_on_sponsors:
            #         pass
            #     else:
            #         unsubscribed += 1
            # if unsubscribed:
            #     await set_unsubscribed(callback.from_user.id, team_unique_code, unsubscribed)
            # else:
            #     await set_unsubscribed(callback.from_user.id, team_unique_code, 0)
            

            result = count - considered - paid
            user_team_data[callback.from_user.id]['result'] = result
        
            getcontext().prec = 10  # Установлює точність
            # amount = (result*price)
            amount = Decimal(str(result)) * Decimal(str(price))
            min_count = (await get_min_count_referrals(team_unique_code))[0]
            if result >= min_count:
                # await add_username(callback.from_user.username, callback.from_user.id)
                await callback.message.answer(
                    str(await gt(callback.message, 'submit_application_message')).format(
                        referrals=result, price=price, amount=amount), parse_mode='Markdown',
                        reply_markup=await go_to_start_team_kb(callback.message)
                )
                await Application.amount.set()
            else:
                await callback.message.answer(str(await gt(callback.message, 'no_applications')).format(min_count=min_count), reply_markup=await go_to_start_team_kb(callback.message), parse_mode='Markdown')
        else:
            await callback.message.answer(str(await gt(callback.message, 'submit_application_error')).format(sponsors=sponsors), reply_markup=await go_to_start_team_kb(callback.message))

async def process_amount(message: types.Message, state: FSMContext):
    result = user_team_data[message.from_user.id]['result']
    reward = user_team_data[message.from_user.id]['reward']
    
    res = Decimal(str(result)) * Decimal(str(reward))
    if message.via_bot:
        if message.via_bot.username == 'send':
            
            match = re.search(r'\$([0-9]+\.[0-9]+|[0-9]+)', message.text)
            if match:
                amount = float(match.group(1))
            else:
                await message.answer(await gt(message, 'url_error'), reply_markup=await go_to_start_team_kb(message))
                return
            
            if amount > float(res):
                await message.answer(str(await gt(message, 'not_enoght_balance')).format(amount = res), reply_markup=await go_to_start_team_kb(message), parse_mode='Markdown')
                await Application.amount.set()
                return
            
            quotient = round(amount / reward)
            if not abs(amount-quotient * reward) < 1e-9:
                await message.answer(str(await gt(message, 'amount_error')).format(reward=reward), reply_markup=await go_to_start_team_kb(message), parse_mode='Markdown')
                await Application.amount.set()
                return
            
            if message.reply_markup:
                url = message.reply_markup.inline_keyboard[0][0].url
                
            count_referrals = int(Decimal(str(amount)) / Decimal(str(reward)))
            min_count = (await get_min_count_referrals(user_team_data[message.from_user.id]['team_unique_code']))[0]
            if count_referrals < min_count:
                await message.answer(str(await gt(message, 'count_referrals_error')).format(min_count=min_count), reply_markup=await go_to_start_team_kb(message), parse_mode='Markdown')
                await Application.amount.set()
                return
            
            success1 = await add_application(
                message.from_user.id, 
                user_team_data[message.from_user.id]['team_unique_code'], 
                message.from_user.username,
                amount, 
                reward, 
                count_referrals,
                url
            )
            success2 = await add_considered(message.from_user.id, user_team_data[message.from_user.id]['team_unique_code'], count_referrals)
            if success1 and success2:
                await message.answer(await gt(message, 'application_submitted'), reply_markup=await go_to_start_team_kb(message))
            else:
                await message.answer(await gt(message, 'application_not_submitted'), reply_markup=await go_to_start_team_kb(message))
    else:
        await message.answer(await gt(message, 'not_send_bot'), reply_markup=await go_to_start_team_kb(message))
        await Application.amount.set()
    
        
    # if message.text.isdigit() and int(message.text)%reward==0 and int(message.text) <= amount:
    #     pass 
    # else:
    #     await message.answer(str(await gt(message, 'amount_error')).format(amount=amount), reply_markup=await go_to_start_team_kb(message))
    #     await Application.amount.set()

class Application(StatesGroup):
    amount = State()
    

async def get_link(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
        personal_link = f'https://t.me/arbitration_assistantbot/?start={team_unique_code}-{callback.from_user.id}'
        await callback.message.answer(str(await gt(callback.message, \
            'personal_link_message')).format(personal_link=personal_link), \
            parse_mode='Markdown', reply_markup=await go_to_start_team_kb(callback.message))


async def add_sponsor(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        await callback.message.answer(await gt(callback.message, 'add_sponsor_message'), reply_markup=await go_to_start_team_kb(callback.message))
        await AddSponsor.link.set()

async def process_sponsor_link(message: types.Message, state: FSMContext):
    if (
        await validate_sponsor_link(message)
    ): 
        await state.update_data(link=message.text)
        await message.answer(await gt(message, 'sponsor_channel_message'), reply_markup=await all_channels_kb(message))
        await AddSponsor.channel_id.set()

async def process_channel_id(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    channel_id = callback.data.split('channel:')[1]
    if channel_id != 'add_temp':
        channel_id = int(channel_id)
    else:
        channel_id = -100
    await success_add_sponsor(callback.message, state, channel_id)
        
async def validate_sponsor_link(message):
    pattern = r"^(https?:\/\/)?(www\.)?t\.me\/[+a-zA-Z0-9_-]{5,32}$"
    if not re.match(pattern, message.text):
        await message.answer(await gt(message, 'sponsor_link_error'), reply_markup=await go_to_start_team_kb(message), parse_mode='Markdown')
        await AddSponsor.link.set()
    else:
        return True

async def success_add_sponsor(message: types.Message, state: FSMContext, channel_id):
        team_unique_code = user_team_data[message.chat.id]['team_unique_code']
        team_name = user_team_data[message.chat.id]['team_name']
        link = (await state.get_data())['link']
        success = await add_sponsor_in_db(team_unique_code, link, channel_id)
        if success:
            await message.answer(await gt(message, 'sponsor_added_message'), reply_markup=await go_to_start_team_kb(message))
            team_members = await get_team_members(team_unique_code)
            for team_memebr in team_members:
                if team_memebr[0] != message.chat.id:
                    try: await bot.send_message(team_memebr[0], str(await gt(message, 'new_sponsor')).format(team=team_name, link=link), parse_mode='Markdown', reply_markup=await fake_check(message))
                    except: pass
        else:
            await message.answer(await gt(message, 'sponsor_not_added_message'), reply_markup=await go_to_start_team_kb(message))
        await state.finish()   

class AddSponsor(StatesGroup):
    link = State()
    channel_id = State()

async def choose_sponsor(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
        sponsors = await get_team_sponsors(team_unique_code)
        if len(sponsors) == 0:
            await callback.message.answer(await gt(callback.message, 'no_sponsors'), reply_markup=await go_to_start_team_kb(callback.message))
        else:
            sponsors = [sponsor for sponsor in sponsors]
            await callback.message.answer(await gt(callback.message, 'choose_sponsor_message'),\
            reply_markup=await get_sponsors_kb(callback.message, sponsors)    
            )
        
async def remove_sponsor(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
        sponsor = callback.data.split('sponsor_')[1]
        
        success = await remove_sponsor_from_db(team_unique_code, sponsor)
        if success:
            await callback.message.answer(await gt(callback.message, 'sponsor_removed_message'), reply_markup=await go_to_start_team_kb(callback.message))
        else:
            await callback.message.answer(await gt(callback.message, 'sponsor_not_removed_message'), reply_markup=await go_to_start_team_kb(callback.message))

async def add_admin(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        await callback.message.answer(await gt(callback.message, 'add_admin_message'), reply_markup=await go_to_start_team_kb(callback.message))
        await AddAdmin.admin_id.set()

async def process_admin_username(message: types.Message, state: FSMContext):
    team_unique_code = user_team_data[message.from_user.id]['team_unique_code']
    if await is_team_member(message.text, team_unique_code):
        success = await update_admin(team_unique_code, message.text)
        if success:
            await message.answer(await gt(message, 'admin_added_message'), reply_markup=await go_to_start_team_kb(message))
    else:
        await message.answer(await gt(message, 'not_team_member'), reply_markup=await go_to_start_team_kb(message))
        await AddAdmin.admin_id.set()

async def choose_admin(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
        admins = await get_admins(team_unique_code)
        if len(admins) == 0:
            await callback.message.answer(await gt(callback.message, 'no_admins'), reply_markup=await go_to_start_team_kb(callback.message))
        else:
            admins = [admin for admin in admins]
            await callback.message.answer(await gt(callback.message, 'choose_admin_message'),\
            reply_markup=await get_admins_kb(callback.message, admins)    
            )
async def remove_admin(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
        admin = callback.data.split('admin_')[1]
        
        success = await remove_admin_from_db(team_unique_code, admin)
        if success:
            await callback.message.answer(await gt(callback.message, 'admin_removed_message'), reply_markup=await go_to_start_team_kb(callback.message))
        else:
            await callback.message.answer(await gt(callback.message, 'admin_not_removed_message'), reply_markup=await go_to_start_team_kb(callback.message))
        

class AddAdmin(StatesGroup):
    admin_id = State()

async def back(callback: types.CallbackQuery, state: FSMContext):
    if callback.message.chat.type == 'private':
        await state.finish()
        callback.data = 'team_' + user_team_data[callback.from_user.id]['team_name']
        await team_start(callback)
      
async def back_to_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.message.chat.type == 'private':
        await state.finish()
        await start(callback)
      
async def my_stats(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        count = user_team_data[callback.from_user.id]['count']
        considered = user_team_data[callback.from_user.id]['considered']
        paid = user_team_data[callback.from_user.id]['paid']
        # unsubscribed = user_team_data[callback.from_user.id]['unsubscribed'] # - paid
        # if unsubscribed < 0:
        #     unsubscribed = 0
        result = count - considered - paid
    
        await callback.message.answer(
            str(await gt(callback.message, 'my_stats_message')).format(count=count,
            considered=considered, paid=paid, result=result), parse_mode='Markdown',
            reply_markup=await my_stats_kb(callback.message)
        )     

async def check_sponsor_subscription(callback: types.CallbackQuery, id_to_check):
    team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
    sponsor_ids = await get_sponsors_ids(team_unique_code)
    sub_on_sponsors = 0
    for sponsor_id in sponsor_ids:
        try:
            member = await bot.get_chat_member(chat_id=sponsor_id[0], user_id=id_to_check)
            if member.is_chat_member():
                sub_on_sponsors += 1
        except Exception as e: 
            sub_on_sponsors += 1
    if sub_on_sponsors == len(sponsor_ids):
        return True
    else:
        return sub_on_sponsors

user_last_interaction = {}
async def update_stats(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        current_time = time.time()
        if callback.from_user.id in user_last_interaction:
            last_interaction_time = user_last_interaction[callback.from_user.id]
            time_diff = current_time - last_interaction_time
            delay = 10
            if time_diff < delay * 60:
                await callback.answer(str(await gt(callback.message, 'update_stats_time_error')).format(time=delay))
                return
        
        await callback.answer(await gt(callback.message, 'updating_stats'))
        team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
        user_referrals = await get_user_referrals(callback.from_user.id, team_unique_code)
        # unsubscribed = 0
        
        # for user_referral in user_referrals:
        #     sub_on_sponsors = await check_sponsor_subscription(callback, user_referral[0])
        #     if isinstance(sub_on_sponsors, bool) and sub_on_sponsors:
        #         pass
        #     else:
        #         unsubscribed += 1
        
        # if unsubscribed:
        #     await set_unsubscribed(callback.from_user.id, team_unique_code, unsubscribed)
        # else:
        #     await set_unsubscribed(callback.from_user.id, team_unique_code, 0)
            
        # user_team_data[callback.from_user.id]['unsubscribed'] = unsubscribed
        user_team_data[callback.from_user.id]['count'] = (await get_user_referrals_count(callback.from_user.id, team_unique_code))[0]
        user_last_interaction[callback.from_user.id] = current_time
        
        await my_stats(callback)

async def set_reward(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        await callback.message.answer(await gt(callback.message, 'set_reward_message'), reply_markup=await go_to_start_team_kb(callback.message))
        await SetReward.reward.set()

async def process_reward(message: types.Message, state: FSMContext):
    try:
        reward = float(message.text)
        success = await update_reward(user_team_data[message.from_user.id]['team_unique_code'], reward)
        if success:
            await message.answer(await gt(message, 'reward_updated_message'), reply_markup=await go_to_start_team_kb(message))
        else:
            await message.answer(await gt(message, 'reward_not_updated_message'), reply_markup=await go_to_start_team_kb(message))
        await state.finish()
    except:
        await message.answer(await gt(message, 'reward_error'), reply_markup=await go_to_start_team_kb(message))
        await SetReward.reward.set()
        return

class SetReward(StatesGroup):
    reward = State()


async def set_min_count(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        await callback.message.answer(await gt(callback.message, 'set_min_count_message'), reply_markup=await go_to_start_team_kb(callback.message))
        await SetMinCount.min_count.set()

async def process_min_count(message: types.Message, state: FSMContext):
    try:
        min_count = int(message.text)
        success = await update_min_count_referrals(user_team_data[message.from_user.id]['team_unique_code'], min_count)
        if success:
            await message.answer(await gt(message, 'min_count_updated_message'), reply_markup=await go_to_start_team_kb(message))
        else:
            await message.answer(await gt(message, 'min_count_not_updated_message'), reply_markup=await go_to_start_team_kb(message))
    except:
        await message.answer(await gt(message, 'min_count_error'), reply_markup=await go_to_start_team_kb(message))
        await SetMinCount.min_count.set()
        return
    
class SetMinCount(StatesGroup):
    min_count = State()    
      
async def payments(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        amount, count = await calculate_amount_and_count(callback)
        await callback.message.answer(
            str(await gt(callback.message, 'payments_message')).format(
                count=count,
                amount = amount    
            ), 
            reply_markup=await choose_filter(callback.message), 
            parse_mode='Markdown'
            )

async def all_payments(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()     
        team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
        applications = await get_applications(team_unique_code)
        await callback.message.answer('============================')
        for application in applications:
            if not application[7]:
                user_id = application[0]
                username = '@' + str(application[2])
                time_joined = (await get_user_time_joined(user_id, team_unique_code))[0]
                count = application[5]
                price = application[4]
                amount = application[3]
                application_time = application[8]
                payment_link = application[6]
                await callback.message.answer(
                    str(await gt(callback.message, 'application_message')).format(
                        user_id=user_id, username=username, time_joined=time_joined, count=count, price=price, amount=amount, application_time=application_time, payment_link=payment_link
                    ), parse_mode='Markdown', disable_web_page_preview=True, reply_markup=await application_management(callback.message, application[9], application[0], application[1], application[5])
                )
        general_amount, general_count = await calculate_amount_and_count(callback)
        global last_message
        last_message = await callback.message.answer(str(await gt(callback.message, 'applications_message')).format(count=general_count, amount=general_amount), reply_markup=await go_to_start_team_kb(callback.message), parse_mode='Markdown')

async def paid_payments(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        amount, count = await calculate_amount_and_count_paid(callback)
        await callback.message.answer(
            str(await gt(callback.message, 'paid_payments_message')).format(
                count=count,
                amount = amount    
            ), 
            reply_markup=await paid_choose_filter(callback.message), 
            parse_mode='Markdown'
            )          

async def all_payments_paid(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.message.delete()     
        team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
        applications = await get_applications(team_unique_code)
        await callback.message.answer('============================')
        for application in applications:
            if application[7]:
                user_id = application[0]
                username = '@' + str(application[2])
                time_joined = (await get_user_time_joined(user_id, team_unique_code))[0]
                count = application[5]
                price = application[4]
                amount = application[3]
                application_time = application[8]
                payment_link = application[6]
                await callback.message.answer(
                    str(await gt(callback.message, 'application_message')).format(
                        user_id=user_id, username=username, time_joined=time_joined, count=count, price=price, amount=amount, application_time=application_time, payment_link=payment_link
                    ), parse_mode='Markdown', disable_web_page_preview=True
                )
        general_amount, general_count = await calculate_amount_and_count_paid(callback, 'by_username')
        await callback.message.answer(str(await gt(callback.message, 'paid_applications_message')).format(count=general_count, amount=general_amount), reply_markup=await go_to_start_team_kb(callback.message), parse_mode='Markdown')

async def calculate_amount_and_count(callback_or_message, username=None):
    team_unique_code = user_team_data[callback_or_message.from_user.id]['team_unique_code']
    if username:
        applications = await get_payments_by_username(username, team_unique_code)
    else:
        applications = await get_applications(team_unique_code)
    amount = 0
    count = 0
    for application in applications:
        if not application[7]:
            amount += application[3]
            count += 1
    return amount, count

async def calculate_amount_and_count_paid(callback: types.CallbackQuery, by_username=None):
    team_unique_code = user_team_data[callback.from_user.id]['team_unique_code']
    applications = await get_applications(team_unique_code)
    amount = 0
    count = 0
    for application in applications:
        if application[7]:
            amount += application[3]
            count += 1
    return amount, count

async def paid(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        success1 = await set_paid_application(callback.data.split(':')[1])
        success2 = await add_paid(callback.data.split(':')[2], callback.data.split(':')[3], callback.data.split(':')[4])
        success3 = await remove_considered(callback.data.split(':')[2], callback.data.split(':')[3], callback.data.split(':')[4])
        if success1 and success2:
            await callback.answer(await gt(callback.message, 'paid_application'))
            amount, count = await calculate_amount_and_count(callback)
            await bot.edit_message_text(
                str(await gt(callback.message, 'applications_message')).format(count=count, amount=amount),
                last_message.chat.id,
                last_message.message_id,
                parse_mode='Markdown',
                reply_markup=await go_to_start_team_kb(callback.message)
            )
            team_name = user_team_data[callback.from_user.id]['team_name']
            await bot.send_message(callback.data.split(':')[2], str(await gt(callback.message, 'paid_application_user')).format(team_name=team_name), parse_mode='Markdown')
            await callback.message.delete()
        else:
            await callback.answer(await gt(callback.message, 'payment_not_set'))

async def delete_application(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        success = await remove_application(callback.data.split(':')[1])
        if success:
            await callback.answer(await gt(callback.message, 'application_deleted'))
            amount, count = await calculate_amount_and_count(callback)
            await bot.edit_message_text(
                str(await gt(callback.message, 'applications_message')).format(count=count, amount=amount),
                last_message.chat.id,
                last_message.message_id,
                parse_mode='Markdown',
                reply_markup=await go_to_start_team_kb(callback.message)
            )
            await callback.message.delete()
        else:
            await callback.answer(await gt(callback.message, 'application_not_deleted'))

async def check(message: types.Message):
    if message.chat.type == 'private':
        if message.from_user.id in AL:
            data = str(message.text.split(' ')[1])
            if data.isdecimal():
                user_id = int(data)
                if await get_user_language(user_id) == None:
                    await message.answer('There is no user with this id in the database')
                    return
            else:
                username = data.replace('@', '')
                print(username)
                user_id = (await get_user_id_by_username(username))
                if user_id == None:
                    await message.answer('There is no user with this username in the database')
                    return
                user_id = user_id[0]
            inviter_id = (await get_inviter_id(user_id, user_team_data[message.from_user.id]['team_unique_code']))[0]
            inviter_username = (await get_inviter_username(inviter_id))[0]
            await message.answer(inviter_username)

async def clear(message: types.Message):
    if message.chat.type == 'private':
        if message.from_user.id in AL:
            all_team_users = await get_all_users('swag')
            for team_user in all_team_users:
                actual_user_referrals = (await get_actual_user_referrals(team_user[0], 'swag'))[0]
                await set_user_referrals_count(team_user[0], 'swag', actual_user_referrals)

async def send_message(message: types.Message, state: FSMContext):
    if message.chat.type == 'private':
        if message.from_user.id in AL:
            await SendMessage.message.set()
            await message.answer('Enter message')

async def process_message(message: types.Message, state: FSMContext):
    users = get_languages()
    print(message.entities)
    print(message.caption)
    # await message.answer_photo(photo=message.photo[-1].file_id, caption=message.caption, parse_mode='HTML')    
    for user_id, language in users:
        try:
            await bot.send_photo(chat_id=user_id, photo=message.photo[-1].file_id, caption=message.caption, parse_mode='HTML')
            # await message.answer_photo(photo=message.photo[-1].file_id, caption=message.caption)
        except Exception as e:
            print('No user with id', user_id)
    await state.finish()
    
class SendMessage(StatesGroup):
    message = State()

async def add_count(message: types.Message):
    if message.chat.type == 'private':
        if message.from_user.id in AL:
            data = message.text.split(' ')
            if len(data) == 3:
                user_id = data[1]
                count = data[2]
                success = await add_count_in_db(user_id, 'swag', count)
                if success:
                    await message.answer('Count updated')
                else:
                    await message.answer('Count not updated')
            else:
                await message.answer('Invalid data')

               
async def set_user_referrals(message: types.Message):
    if message.chat.type == 'private':
        if message.from_user.id in AL:
            data = message.text.split(' ')
            if len(data) == 7:
                user_id = data[1]
                team_unique_code = data[2]
                referral_count = data[3]
                unsubscribed = data[4]
                considered = data[5]
                paid = data[6]
                success = await set_user_referrals_in_db(user_id, team_unique_code, referral_count, unsubscribed, considered, paid)
                if success:
                    await message.answer('Referrals count updated')
                else:
                    await message.answer('Referrals count not updated')
            else:
                await message.answer('Invalid data')
        else:
            await message.answer('You are not allowed to use this command')
             
async def add_allow_team(message: types.Message):
    if message.chat.type == 'private':
        if message.from_user.id in AL:
            user_id = message.text.split(' ')[1]
            if await get_user_language(user_id) == None:
                await message.answer('There is no user with this id in the database')
                return
            success = await add_allow_team_in_db(user_id)
            if success:
                await message.answer('User added 1 permission to create a team')
        else:
            await message.answer('You are not allowed to use this command')

async def notify_restart(message: types.Message):
    if message.chat.type == 'private':
        if message.from_user.id in AL:
            users = get_languages()
            for user_id, language in users:
                if language == 'uk':
                    text = "Бот був перезапущений, тому попередня сесія була завершена (через це кнопки на старих повідомленням можуть не працювати)\nПочніть нову сесію командою /start"
                else:
                    text = "Бот был перезапущен, поэтому прошлая сессия была завершена (из-за этого кнопки на старых сообщениях могут не работать)\nНачните новую сессия командой /start"
                try:
                    await bot.send_message(user_id, text)
                except Exception as e:
                    pass

async def by_id_payments(callback: types.CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.answer(await gt(callback.message, 'temp'))

async def by_username_payments(callback: types.CallbackQuery, state: FSMContext):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        await PaymentUsername.username.set()
        await callback.message.answer(await gt(callback.message, 'enter_username'), reply_markup=await go_to_start_team_kb(callback.message))

async def process_username(message: types.Message, state: FSMContext):
    username_raw = message.text.replace('@', '')
    team_unique_code = user_team_data[message.from_user.id]['team_unique_code']
    applications = await get_payments_by_username(username_raw, team_unique_code)
    await message.answer('============================')
    for application in applications:
        if not application[7]:
            user_id = application[0]
            username = '@' + str(application[2])
            time_joined = (await get_user_time_joined(user_id, team_unique_code))[0]
            count = application[5]
            price = application[4]
            amount = application[3]
            application_time = application[8]
            payment_link = application[6]
            await message.answer(
                str(await gt(message, 'application_message')).format(
                    user_id=user_id, username=username, time_joined=time_joined, count=count, price=price, amount=amount, application_time=application_time, payment_link=payment_link
                ), parse_mode='Markdown', disable_web_page_preview=True, reply_markup=await application_management(message, application[9], application[0], application[1], application[5])
            )
    general_amount, general_count = await calculate_amount_and_count(message, username_raw)
    global last_message
    last_message = await message.answer(str(await gt(message, 'applications_message')).format(count=general_count, amount=general_amount), reply_markup=await go_to_start_team_kb(message), parse_mode='Markdown')
class PaymentUsername(StatesGroup):
    username = State()

async def add_channel_handler(update: types.ChatMemberUpdated):
    success = False
    if update.new_chat_member.status == 'administrator':
        chat_id = update.chat.id
        chat_name = update.chat.title
        success = await add_channel(chat_id, chat_name)
    if success:
        user_id = update.from_user.id
        mess = f'Your channel *{chat_name}* added to the database. Thanks!'
    else:
        mess = 'An unknown error has occurred, your channel has not been added to the database. Contact the admin'
    try:
        await bot.send_message(user_id, mess, parse_mode='Markdown')
    except:
        pass

async def add_chat_handler(message: types.Message):
    for new_member in message.new_chat_members:
        if new_member.id == message.bot.id:
            chat_id = message.chat.id
            chat_title = message.chat.title
            success = await add_channel(chat_id, chat_title)
    if success:
        mess = f'Your chat *{chat_title}* added to the database. Thanks!'
    else:
        mess = 'An unknown error has occurred, your chat has not been added to the database. Contact the admin'
    try:
        await bot.send_message(message.from_user.id, mess, parse_mode='Markdown')
    except:
        pass
    
def register_handlers_private(dp: Dispatcher):
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(check, commands=['check'])
    dp.register_message_handler(clear, commands=['clear'])
    dp.register_message_handler(send_message, commands=['send_message'])
    dp.register_message_handler(process_message, state=SendMessage.message, content_types=types.ContentTypes.ANY)
    dp.register_message_handler(add_count, commands=['add_count'])
    dp.register_message_handler(set_user_referrals, commands=['set_user_referrals'])
    dp.register_message_handler(add_allow_team, commands=['add_allow_team'])
    dp.register_message_handler(notify_restart, commands=['notify_restart'])
    dp.register_callback_query_handler(back, text='teamstart', state='*')
    dp.register_callback_query_handler(start, text='start')
    dp.register_callback_query_handler(choose_language, text='change_language')
    dp.register_callback_query_handler(team_start, filters.Regexp(r'^team_'))
    dp.register_message_handler(create_team, commands=['create_team'])
    dp.register_callback_query_handler(create_team, text='create_team')
    dp.register_message_handler(process_team_name, state=CreateTeam.team_name)
    dp.register_message_handler(process_team_unique_code, state=CreateTeam.team_unique_code)
    dp.register_callback_query_handler(process_team_confirmation, state=CreateTeam.confirmation)
    dp.register_callback_query_handler(get_link, text='get_link')
    dp.register_callback_query_handler(back_to_start, text='back', state='*')
    dp.register_callback_query_handler(add_sponsor, text='add_sponsor')
    dp.register_message_handler(process_sponsor_link, state=AddSponsor.link)
    dp.register_callback_query_handler(process_channel_id, filters.Regexp(r'^channel:'), state=AddSponsor.channel_id)
    # dp.register_message_handler(process_channel_id, filters.Regexp(r'^channel:'))
    dp.register_callback_query_handler(choose_sponsor, text='remove_sponsor')
    dp.register_callback_query_handler(remove_sponsor, filters.Regexp(r'^sponsor_'))
    dp.register_callback_query_handler(remove_admin, filters.Regexp(r'^admin_'))
    dp.register_callback_query_handler(set_reward, text='set_reward')
    dp.register_message_handler(process_reward, state=SetReward.reward)
    dp.register_callback_query_handler(add_admin, text='add_admin')
    dp.register_message_handler(process_admin_username, state=AddAdmin.admin_id)
    dp.register_callback_query_handler(choose_admin, text='remove_admin')
    dp.register_callback_query_handler(check_sub, text='check_sub') 
    dp.register_callback_query_handler(fake_check_sub, text='fake_check_sub') 
    dp.register_callback_query_handler(my_stats, text='my_stats')
    dp.register_callback_query_handler(update_stats, text='update_stats')
    dp.register_callback_query_handler(management, text='management')
    dp.register_callback_query_handler(global_statistic, text='global_statistic')
    dp.register_callback_query_handler(submit_application, text='submit_application')
    dp.register_message_handler(process_amount, state=Application.amount) 
    dp.register_callback_query_handler(payments, text='payments')
    dp.register_callback_query_handler(all_payments, text='all')
    dp.register_callback_query_handler(by_id_payments, text='by_id')
    dp.register_callback_query_handler(by_username_payments, text='by_username') 
    dp.register_message_handler(process_username, state=PaymentUsername.username) 
    dp.register_callback_query_handler(paid, filters.Regexp(r'^paid:'))
    dp.register_callback_query_handler(delete_application, filters.Regexp(r'^delete:'))
    dp.register_callback_query_handler(set_min_count, text='set_min_count')
    dp.register_message_handler(process_min_count, state=SetMinCount.min_count)
    dp.register_my_chat_member_handler(add_channel_handler)
    dp.register_message_handler(add_chat_handler, content_types=types.ContentTypes.NEW_CHAT_MEMBERS) 
    # dp.register_message_handler(process_min_count, state=SetMinCount.min_count) 
    dp.register_callback_query_handler(paid_payments, text='paid_payments')
    dp.register_callback_query_handler(all_payments_paid, text='all_paid')