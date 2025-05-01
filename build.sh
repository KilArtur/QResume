#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Запуск проекта QResume${NC}"

# Проверка наличия необходимых директорий
if [ ! -d "server" ] || [ ! -d "front" ]; then
    echo "Ошибка: Не найдены директории server или front"
    exit 1
fi

# Установка зависимостей для бэкенда
echo -e "${BLUE}Установка зависимостей для бэкенда...${NC}"
cd server
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Ошибка: Не удалось установить зависимости для бэкенда"
    exit 1
fi

# Проверка, не занят ли порт 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${BLUE}Порт 8000 уже используется. Останавливаем процесс...${NC}"
    fuser -k 8000/tcp
    sleep 2
fi

# Запуск бэкенда в фоновом режиме
echo -e "${BLUE}Запуск бэкенда...${NC}"
cd src
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug &
BACKEND_PID=$!
cd ../..

# Проверка, что бэкенд запустился
sleep 3
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "Ошибка: Не удалось запустить бэкенд"
    exit 1
fi

echo -e "${GREEN}Бэкенд успешно запущен на http://localhost:8000${NC}"

# Запуск фронтенда в фоновом режиме
echo -e "${BLUE}Запуск фронтенда...${NC}"
cd front
python -m http.server 8080 &
FRONTEND_PID=$!
cd ..

# Проверка, что фронтенд запустился
sleep 2
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "Ошибка: Не удалось запустить фронтенд"
    kill $BACKEND_PID
    exit 1
fi

echo -e "${GREEN}Фронтенд успешно запущен на http://localhost:8080${NC}"
echo -e "${GREEN}Приложение доступно по адресу: http://localhost:8080${NC}"
echo -e "${BLUE}Для остановки приложения нажмите Ctrl+C${NC}"

# Функция для корректного завершения процессов при выходе
cleanup() {
    echo -e "${BLUE}Остановка приложения...${NC}"
    kill $BACKEND_PID
    kill $FRONTEND_PID
    echo -e "${GREEN}Приложение остановлено${NC}"
    exit 0
}

# Регистрация обработчика сигнала для корректного завершения
trap cleanup SIGINT SIGTERM

# Ожидание завершения
wait
