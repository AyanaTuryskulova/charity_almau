from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import sqlite3
import asyncio
from dotenv import load_dotenv


load_dotenv() 
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID")) 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключениемся к базе данных
conn = sqlite3.connect("donations.db")
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS donations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    description TEXT,
                    photo TEXT
                )''')
conn.commit()


class AddItemState(StatesGroup):
    waiting_for_photo = State()
    waiting_for_description = State()

# возможность кнопок менюшки
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить вещь")],
        [KeyboardButton(text="📦 Посмотреть доступные вещи")]
    ],
    resize_keyboard=True
)

@dp.message(F.text == "/start")
async def start(message: types.Message):
    await message.answer("Привет! Здесь ты можешь оставить ненужные вещи для благотворительности или забрать что-то нужное", reply_markup=main_kb)

@dp.message(F.text == "➕ Добавить вещь")
async def add_item(message: types.Message, state: FSMContext):
    await message.answer("Отправь фото вещи")
    await state.set_state(AddItemState.waiting_for_photo)

@dp.message(F.photo, AddItemState.waiting_for_photo)
async def handle_photo(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(photo=file_id)
    await message.answer("Теперь отправь описание вещи")
    await state.set_state(AddItemState.waiting_for_description)

@dp.message(AddItemState.waiting_for_description)
async def handle_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = data["photo"]

    # Сохраняем данные в БД
    cursor.execute("INSERT INTO donations (user_id, description, photo) VALUES (?, ?, ?)", 
                   (message.from_user.id, message.text, photo_id))
    conn.commit()

    await message.answer("✅ Вещь добавлена! Теперь она доступна для просмотра", reply_markup=main_kb)
    await state.clear()

@dp.message(F.text == "📦 Посмотреть доступные вещи")
async def show_items(message: types.Message):
    cursor.execute("SELECT id, user_id, description, photo FROM donations")
    items = cursor.fetchall()
    
    if not items:
        await message.answer("❌ Пока нет доступных вещей")
        return

    for item_id, user_id, desc, photo in items:
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛍 Забрать", callback_data=f"take_{item_id}")]
        ])

        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=f"🆔 {item_id} | {desc}", reply_markup=inline_kb)

@dp.callback_query(F.data.startswith("take_"))
async def take_item(callback: types.CallbackQuery):
    try:
        item_id = int(callback.data.split("_")[1])
        cursor.execute("SELECT user_id FROM donations WHERE id = ?", (item_id,))
        owner_id = cursor.fetchone()

        if owner_id:
            owner_id = owner_id[0]
            user = await bot.get_chat(owner_id)

            await callback.answer()

            # Проверяем, есть ли у владельца username
            if user.username:
                contact_info = f"Свяжись с владельцем: @{user.username}"
            else:
                contact_info = f"Свяжись с владельцем: [tg://user?id={owner_id}]"

            await callback.message.answer(contact_info)
        else:
            await callback.answer("❌ Этот товар больше недоступен")
    except Exception as e:
        print(f"Ошибка при обработке кнопки 'Забрать': {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

# удаление только для меня как админа
@dp.message(F.text.startswith("/delete"))
async def delete_item(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для удаления вещей")
        return

    try:
        item_id = int(message.text.split()[1])  # Получаем ID товара
        cursor.execute("DELETE FROM donations WHERE id = ?", (item_id,))
        conn.commit()

        await message.answer(f"✅ Вещь с ID {item_id} удалена")
    except (IndexError, ValueError):
        await message.answer("❌ Используйте команду правильно: `/delete ID_вещи`")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
