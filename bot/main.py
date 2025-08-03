#!/usr/bin/env python3
"""
Main Telegram bot for HelpDesk Ecosystem
Cartridge management system
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Import our database utilities
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_utils import (
    user_manager, branch_manager, cartridge_manager, 
    request_manager, log_manager, generate_request_code
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_here')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]

# FSM States
class RequestStates(StatesGroup):
    """States for request creation flow"""
    selecting_branch = State()
    selecting_priority = State()
    selecting_cartridges = State()
    entering_quantity = State()
    adding_comment = State()
    confirming_request = State()

class BotManager:
    """Main bot manager class"""
    
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        
        # Command handlers
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_new_request, Command("new"))
        self.dp.message.register(self.cmd_my_requests, Command("my"))
        
        # Admin commands
        self.dp.message.register(self.cmd_admin, Command("admin"))
        self.dp.message.register(self.cmd_stats, Command("stats"))
        
        # Callback handlers
        self.dp.callback_query.register(self.handle_branch_selection)
        self.dp.callback_query.register(self.handle_priority_selection)
        self.dp.callback_query.register(self.handle_cartridge_selection)
        self.dp.callback_query.register(self.handle_confirm_request)
        
        # Message handlers
        self.dp.message.register(self.handle_quantity_input, RequestStates.entering_quantity)
        self.dp.message.register(self.handle_comment_input, RequestStates.adding_comment)
    
    async def cmd_start(self, message: types.Message):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        
        # Check if user exists, create if not
        user = user_manager.get_user_by_telegram_id(user_id)
        if not user:
            user_manager.create_user(user_id, username)
            await message.answer(
                f"👋 Добро пожаловать в систему заказа картриджей!\n"
                f"Ваш аккаунт создан. Используйте /new для создания заявки."
            )
        else:
            await message.answer(
                f"👋 С возвращением, {username}!\n"
                f"Используйте /new для создания новой заявки на картриджи."
            )
    
    async def cmd_help(self, message: types.Message):
        """Handle /help command"""
        help_text = """
🤖 **Система заказа картриджей**

**Основные команды:**
• `/new` - Создать новую заявку
• `/my` - Мои заявки
• `/help` - Эта справка

**Процесс заказа:**
1. Выберите филиал
2. Укажите приоритет
3. Выберите картриджи и количество
4. Добавьте комментарий (опционально)
5. Подтвердите заявку

**Статусы заявок:**
• 🆕 Новый
• ⏳ В работе
• ✅ Выполнено
• ❌ Отменено
• 📁 Архив

По всем вопросам обращайтесь к администратору.
        """
        await message.answer(help_text, parse_mode="Markdown")
    
    async def cmd_new_request(self, message: types.Message):
        """Start new request creation"""
        user_id = message.from_user.id
        
        # Check if user exists
        user = user_manager.get_user_by_telegram_id(user_id)
        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start для регистрации.")
            return
        
        # Get branches for selection
        branches = branch_manager.get_all_branches()
        if not branches:
            await message.answer("❌ Нет доступных филиалов.")
            return
        
        # Create branch selection keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{branch['name']} ({branch['code']})", 
                                callback_data=f"branch:{branch['id']}")]
            for branch in branches
        ])
        
        await message.answer(
            "🏢 **Выберите филиал:**\n\n"
            "Выберите филиал, для которого создается заявка:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await RequestStates.selecting_branch.set()
    
    async def handle_branch_selection(self, callback: types.CallbackQuery, state: FSMContext):
        """Handle branch selection"""
        branch_id = int(callback.data.split(':')[1])
        
        # Store branch_id in state
        await state.update_data(branch_id=branch_id)
        
        # Create priority selection keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Низкий", callback_data="priority:low")],
            [InlineKeyboardButton(text="🟡 Обычный", callback_data="priority:normal")],
            [InlineKeyboardButton(text="🔴 Высокий", callback_data="priority:high")]
        ])
        
        await callback.message.edit_text(
            "⚡ **Выберите приоритет заявки:**\n\n"
            "🟢 Низкий - обычная заявка\n"
            "🟡 Обычный - стандартный приоритет\n"
            "🔴 Высокий - срочная заявка",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await RequestStates.selecting_priority.set()
        await callback.answer()
    
    async def handle_priority_selection(self, callback: types.CallbackQuery, state: FSMContext):
        """Handle priority selection"""
        priority = callback.data.split(':')[1]
        
        # Store priority in state
        await state.update_data(priority=priority)
        
        # Get cartridges for selection
        cartridges = cartridge_manager.get_all_cartridge_types()
        if not cartridges:
            await callback.message.edit_text("❌ Нет доступных картриджей.")
            return
        
        # Create cartridge selection keyboard (first 10)
        keyboard_buttons = []
        for cartridge in cartridges[:10]:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{cartridge['name']} ({cartridge['sku']})", 
                    callback_data=f"cartridge:{cartridge['id']}"
                )
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            "🖨️ **Выберите картридж:**\n\n"
            "Выберите тип картриджа для заказа:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await RequestStates.selecting_cartridges.set()
        await callback.answer()
    
    async def handle_cartridge_selection(self, callback: types.CallbackQuery, state: FSMContext):
        """Handle cartridge selection"""
        cartridge_id = int(callback.data.split(':')[1])
        
        # Store cartridge_id in state
        await state.update_data(cartridge_id=cartridge_id)
        
        await callback.message.edit_text(
            "🔢 **Введите количество:**\n\n"
            "Укажите количество картриджей для заказа:",
            parse_mode="Markdown"
        )
        await RequestStates.entering_quantity.set()
        await callback.answer()
    
    async def handle_quantity_input(self, message: types.Message, state: FSMContext):
        """Handle quantity input"""
        try:
            quantity = int(message.text)
            if quantity <= 0:
                await message.answer("❌ Количество должно быть больше 0.")
                return
            
            # Store quantity in state
            await state.update_data(quantity=quantity)
            
            await message.answer(
                "💬 **Добавьте комментарий (опционально):**\n\n"
                "Введите комментарий к заявке или отправьте '-' для пропуска:",
                parse_mode="Markdown"
            )
            await RequestStates.adding_comment.set()
            
        except ValueError:
            await message.answer("❌ Пожалуйста, введите целое число.")
    
    async def handle_comment_input(self, message: types.Message, state: FSMContext):
        """Handle comment input"""
        comment = message.text if message.text != '-' else None
        
        # Store comment in state
        await state.update_data(comment=comment)
        
        # Get all data from state
        data = await state.get_data()
        
        # Get additional info for confirmation
        branch = branch_manager.get_all_branches()
        branch = next((b for b in branch if b['id'] == data['branch_id']), None)
        
        cartridge = cartridge_manager.get_all_cartridge_types()
        cartridge = next((c for c in cartridge if c['id'] == data['cartridge_id']), None)
        
        if not branch or not cartridge:
            await message.answer("❌ Ошибка: данные не найдены.")
            await state.clear()
            return
        
        # Create confirmation message
        priority_emoji = {
            'low': '🟢',
            'normal': '🟡', 
            'high': '🔴'
        }
        
        confirmation_text = f"""
📋 **Подтверждение заявки:**

🏢 **Филиал:** {branch['name']} ({branch['code']})
⚡ **Приоритет:** {priority_emoji[data['priority']]} {data['priority'].title()}
🖨️ **Картридж:** {cartridge['name']} ({cartridge['sku']})
🔢 **Количество:** {data['quantity']} шт.
💬 **Комментарий:** {comment or 'Не указан'}

Всё верно?
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm:yes")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="confirm:no")]
        ])
        
        await message.answer(confirmation_text, reply_markup=keyboard, parse_mode="Markdown")
        await RequestStates.confirming_request.set()
    
    async def handle_confirm_request(self, callback: types.CallbackQuery, state: FSMContext):
        """Handle request confirmation"""
        if callback.data == "confirm:no":
            await callback.message.edit_text("❌ Заявка отменена.")
            await state.clear()
            await callback.answer()
            return
        
        # Get data from state
        data = await state.get_data()
        user_id = callback.from_user.id
        
        try:
            # Generate request code
            request_code = generate_request_code()
            
            # Create request
            request_id = request_manager.create_request(
                request_code=request_code,
                branch_id=data['branch_id'],
                user_id=user_id,
                priority=data['priority'],
                comment=data['comment']
            )
            
            # Add request items
            request_manager.add_request_items(
                request_id=request_id,
                items=[(data['cartridge_id'], data['quantity'])]
            )
            
            # Log the creation
            log_manager.add_log(
                request_id=request_id,
                user_id=user_id,
                action='created',
                note='Заявка создана через Telegram бота'
            )
            
            # Success message
            success_text = f"""
✅ **Заявка создана успешно!**

📋 **Номер заявки:** `{request_code}`
🏢 **Филиал:** {data.get('branch_name', 'N/A')}
⚡ **Приоритет:** {data['priority'].title()}
📅 **Дата создания:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

Ваша заявка принята в обработку. 
Используйте /my для просмотра ваших заявок.
            """
            
            await callback.message.edit_text(success_text, parse_mode="Markdown")
            
            # Notify admins about new request
            await self.notify_admins_new_request(request_code, data)
            
        except Exception as e:
            logger.error(f"Error creating request: {e}")
            await callback.message.edit_text("❌ Ошибка при создании заявки. Попробуйте позже.")
        
        await state.clear()
        await callback.answer()
    
    async def cmd_my_requests(self, message: types.Message):
        """Show user's requests"""
        user_id = message.from_user.id
        
        # Get user
        user = user_manager.get_user_by_telegram_id(user_id)
        if not user:
            await message.answer("❌ Пользователь не найден.")
            return
        
        # Get user's requests
        requests = request_manager.get_user_requests(user['id'], limit=5)
        
        if not requests:
            await message.answer("📭 У вас пока нет заявок. Используйте /new для создания.")
            return
        
        # Format requests
        requests_text = "📋 **Ваши последние заявки:**\n\n"
        
        for req in requests:
            status_emoji = {
                'new': '🆕',
                'in_progress': '⏳',
                'done': '✅',
                'cancelled': '❌',
                'archived': '📁'
            }
            
            requests_text += f"""
{status_emoji.get(req['status'], '❓')} **{req['request_code']}**
🏢 {req['branch_name']} ({req['branch_code']})
⚡ {req['priority'].title()}
📅 {req['created_at'][:10]}
📊 Статус: {req['status'].replace('_', ' ').title()}
            """
        
        await message.answer(requests_text, parse_mode="Markdown")
    
    async def cmd_admin(self, message: types.Message):
        """Admin panel"""
        user_id = message.from_user.id
        
        if user_id not in ADMIN_IDS:
            await message.answer("❌ Доступ запрещен.")
            return
        
        # Admin panel logic here
        await message.answer("🔧 Панель администратора\n\nИспользуйте /stats для статистики.")
    
    async def cmd_stats(self, message: types.Message):
        """Show statistics"""
        user_id = message.from_user.id
        
        if user_id not in ADMIN_IDS:
            await message.answer("❌ Доступ запрещен.")
            return
        
        # Get basic stats
        stats = self.get_basic_stats()
        
        stats_text = f"""
📊 **Статистика системы:**

👥 **Пользователи:** {stats['users']}
🏢 **Филиалы:** {stats['branches']}
🖨️ **Типы картриджей:** {stats['cartridges']}
📋 **Заявки:** {stats['requests']}
🆕 **Новые заявки:** {stats['new_requests']}
⏳ **В работе:** {stats['in_progress']}
✅ **Выполнено:** {stats['completed']}
        """
        
        await message.answer(stats_text, parse_mode="Markdown")
    
    def get_basic_stats(self) -> Dict[str, int]:
        """Get basic system statistics"""
        # This would be implemented with actual database queries
        return {
            'users': 0,
            'branches': 0,
            'cartridges': 0,
            'requests': 0,
            'new_requests': 0,
            'in_progress': 0,
            'completed': 0
        }
    
    async def notify_admins_new_request(self, request_code: str, data: Dict[str, Any]):
        """Notify admins about new request"""
        if not ADMIN_IDS:
            return
        
        notification_text = f"""
🆕 **Новая заявка!**

📋 **Номер:** `{request_code}`
🏢 **Филиал:** {data.get('branch_name', 'N/A')}
⚡ **Приоритет:** {data['priority'].title()}
🕐 **Время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        for admin_id in ADMIN_IDS:
            try:
                await self.bot.send_message(admin_id, notification_text, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    async def start(self):
        """Start the bot"""
        logger.info("Starting bot...")
        await self.dp.start_polling(self.bot)

async def main():
    """Main function"""
    bot_manager = BotManager()
    await bot_manager.start()

if __name__ == "__main__":
    asyncio.run(main())