#!/bin/bash

# --- НАСТРОЙКИ ---
REPO_URL="https://github.com/Rewixx-png/telegram-feedback-bot.git"
PROJECT_FOLDER="telegram-feedback-bot"

# --- ЦВЕТА ДЛЯ ВЫВОДА ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- ФУНКЦИЯ ДЛЯ ВЫВОДА ОШИБКИ И ВЫХОДА ---
function error_exit {
    echo -e "${RED}ОШИБКА: $1${NC}" >&2
    exit 1
}

clear
echo -e "${GREEN}--- Универсальный установщик Feedback Bot (без venv) ---${NC}"
echo "Этот скрипт автоматически загрузит, настроит и подготовит к запуску вашего бота."
echo ""

# --- 1. Проверка зависимостей ---
echo "--> Проверка необходимых утилит..."
command -v git &> /dev/null || error_exit "Git не установлен. Пожалуйста, установите его (например, 'sudo apt install git')."
command -v python3 &> /dev/null || error_exit "Python 3 не установлен. Пожалуйста, установите его."
command -v pip3 &> /dev/null || error_exit "pip3 не установлен. Пожалуйста, установите его (например, 'sudo apt install python3-pip')."
command -v npm &> /dev/null || error_exit "NPM (Node.js) не установлен. Он нужен для PM2. Установите его."
echo -e "${GREEN}Все базовые утилиты на месте.${NC}"
echo ""

# --- 2. Установка PM2 (если необходимо) ---
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}Менеджер процессов PM2 не найден.${NC}"
    read -p "Хотите установить его глобально через npm? [Y/n]: " confirm_pm2
    if [[ "$confirm_pm2" =~ ^[yY](es)?$ || -z "$confirm_pm2" ]]; then
        echo "--> Устанавливаю PM2..."
        sudo npm install pm2 -g || error_exit "Не удалось установить PM2."
        echo -e "${GREEN}PM2 успешно установлен.${NC}"
    else
        error_exit "Установка прервана. PM2 необходим для работы."
    fi
else
    echo -e "${GREEN}PM2 уже установлен.${NC}"
fi
echo ""

# --- 3. Выбор директории для установки ---
read -p "Укажите путь для установки бота (по умолчанию: /root): " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-/root}

mkdir -p "$INSTALL_DIR" || error_exit "Не удалось создать директорию $INSTALL_DIR."
cd "$INSTALL_DIR" || error_exit "Не удалось перейти в директорию $INSTALL_DIR."

echo "--> Установка будет произведена в: ${GREEN}$(pwd)${NC}"
echo ""

# --- 4. Клонирование репозитория ---
if [ -d "$PROJECT_FOLDER" ]; then
    echo -e "${YELLOW}Папка '$PROJECT_FOLDER' уже существует.${NC}"
    read -p "Хотите удалить ее и скачать заново? (Все данные в ней будут стерты!) [y/N]: " confirm_delete
    if [[ "$confirm_delete" =~ ^[yY](es)?$ ]]; then
        rm -rf "$PROJECT_FOLDER"
    else
        error_exit "Установка прервана."
    fi
fi

echo "--> Клонирую репозиторий..."
git clone "$REPO_URL" || error_exit "Не удалось склонировать репозиторий."
cd "$PROJECT_FOLDER" || error_exit "Не удалось перейти в папку проекта."
APP_PATH=$(pwd)

# --- 5. Сбор данных от пользователя ---
echo ""
echo -e "${GREEN}Пожалуйста, введите данные для настройки бота:${NC}"

while [ -z "$BOT_TOKEN" ]; do
    read -p "Введите токен вашего бота от @BotFather: " BOT_TOKEN
done

while [ -z "$OWNER_ID" ]; do
    read -p "Введите ваш числовой Telegram ID (узнать у @userinfobot): " OWNER_ID
    [[ "$OWNER_ID" =~ ^[0-9]+$ ]] || { echo -e "${YELLOW}ID должен быть числом!${NC}"; OWNER_ID=""; }
done

while [ -z "$LOG_CHAT_ID" ]; do
    read -p "Введите ID чата для логов (отрицательное число, например -100...): " LOG_CHAT_ID
    [[ "$LOG_CHAT_ID" =~ ^-100[0-9]+$ ]] || { echo -e "${YELLOW}ID чата должен быть отрицательным числом, начинающимся с -100...${NC}"; LOG_CHAT_ID=""; }
done

echo ""
echo -e "${GREEN}Отлично! Начинаю настройку файлов...${NC}"

# --- 6. Настройка проекта ---
echo "$BOT_TOKEN" > token.txt
sed -i "s/OWNER_ID\s*=\s*[0-9]*/OWNER_ID    = $OWNER_ID/" main.py
sed -i "s/LOG_CHAT_ID\s*=\s*-[0-9]*/LOG_CHAT_ID = $LOG_CHAT_ID/" main.py

echo "--> Устанавливаю зависимости для текущего пользователя (pip3 install --user)..."
pip3 install --user -r requirements.txt || error_exit "Не удалось установить зависимости."

# --- 7. Настройка PM2 ---
BOT_NAME="feedback-bot-$(basename $APP_PATH)"
PYTHON_PATH=$(command -v python3) # Находим системный python3
echo "--> Создаю конфигурационный файл для PM2 (ecosystem.config.js)..."

cat <<EOF > ecosystem.config.js
module.exports = {
  apps : [{
    name   : "$BOT_NAME",
    script : "main.py",
    interpreter: "$PYTHON_PATH",
    cwd: "$APP_PATH"
  }]
}
EOF

# --- 8. Финальные инструкции ---
echo ""
echo -e "${GREEN}🎉 Установка успешно завершена! 🎉${NC}"
echo "Бот был установлен в директорию: ${YELLOW}$APP_PATH${NC}"
echo "Процесс для PM2 был назван: ${YELLOW}$BOT_NAME${NC}"
echo ""
echo -e "${YELLOW}--- Как запустить и использовать бота ---${NC}"
echo "1. Перейдите в папку с ботом:"
echo -e "   ${GREEN}cd $APP_PATH${NC}"
echo ""
echo "2. Чтобы запустить бота, выполните команду:"
echo -e "   ${GREEN}pm2 start ecosystem.config.js${NC}"
echo ""
echo "3. Чтобы бот запускался автоматически после перезагрузки сервера:"
echo -e "   ${GREEN}pm2 save${NC}"
echo -e "   ${GREEN}pm2 startup${NC} (и выполните команду, которую она вам покажет)"
echo ""
echo "4. Полезные команды PM2:"
echo -e "   - Посмотреть логи: ${GREEN}pm2 logs $BOT_NAME${NC}"
echo -e "   - Остановить бота: ${GREEN}pm2 stop $BOT_NAME${NC}"
echo -e "   - Перезапустить бота: ${GREEN}pm2 restart $BOT_NAME${NC}"
echo -e "   - Список всех процессов: ${GREEN}pm2 list${NC}"
echo ""
echo "Удачи!"