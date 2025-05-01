document.addEventListener('DOMContentLoaded', function() {
    // Элементы интерфейса
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const currentTechnology = document.getElementById('currentTechnology');
    const currentQuestion = document.getElementById('currentQuestion');
    const answerInput = document.getElementById('answerInput');
    const prevQuestionBtn = document.getElementById('prevQuestionBtn');
    const nextQuestionBtn = document.getElementById('nextQuestionBtn');
    const finishInterviewBtn = document.getElementById('finishInterviewBtn');
    const interviewResults = document.getElementById('interviewResults');
    const resultsContainer = document.getElementById('resultsContainer');
    const returnToMainBtn = document.getElementById('returnToMainBtn');
    const interviewCard = document.querySelector('.interview-card');
    const candidateName = document.getElementById('candidateName');
    const candidatePosition = document.getElementById('candidatePosition');
    
    // Получаем данные из localStorage
    let questions = [];
    let candidateInfo = {};
    
    try {
        console.log('Пытаемся загрузить данные из localStorage');
        
        // Проверяем, что localStorage содержит необходимые данные
        const storedData = localStorage.getItem('interviewData');
        if (!storedData) {
            throw new Error('Данные для собеседования не найдены в localStorage');
        }
        
        console.log('Данные найдены в localStorage:', storedData.substring(0, 100) + '...');
        questions = JSON.parse(storedData);
        
        candidateInfo = JSON.parse(localStorage.getItem('candidateInfo') || '{}');
        
        // Загружаем полные данные анализа резюме
        const resumeAnalysisData = localStorage.getItem('resumeAnalysisData');
        if (resumeAnalysisData) {
            console.log('Загружены полные данные анализа резюме');
            window.resumeAnalysisData = JSON.parse(resumeAnalysisData);
            
            // Проверяем, есть ли в данных анализа вопросы по технологиям
            const analysisData = JSON.parse(resumeAnalysisData);
            if (analysisData.questions_by_technology && Array.isArray(analysisData.questions_by_technology)) {
                console.log('Используем вопросы из анализа резюме');
                
                // Если в localStorage нет вопросов или их мало, используем вопросы из анализа
                if (!questions.length || questions.length < 5) {
                    questions = [];
                    analysisData.questions_by_technology.forEach(tech => {
                        const technology = tech.name_technology || 'Неизвестная технология';
                        
                        for (let i = 1; i <= 5; i++) {
                            const questionKey = `question${i}`;
                            if (tech[questionKey] && typeof tech[questionKey] === 'string') {
                                questions.push({
                                    technology: technology,
                                    question: tech[questionKey],
                                    answer: '',
                                    questionNumber: i
                                });
                            }
                        }
                    });
                    
                    // Сохраняем обновленные вопросы в localStorage
                    localStorage.setItem('interviewData', JSON.stringify(questions));
                    console.log('Обновлены вопросы из анализа резюме, всего:', questions.length);
                }
            }
        }
        
        // Проверяем, что у нас есть вопросы
        if (!questions.length) {
            throw new Error('Список вопросов пуст');
        }
        
        console.log('Загружено вопросов:', questions.length);
        
        // Скрываем информацию о кандидате, так как она не нужна
        if (candidateName) candidateName.style.display = 'none';
        if (candidatePosition) candidatePosition.style.display = 'none';
        
    } catch (e) {
        console.error('Ошибка при загрузке данных:', e);
        alert('Ошибка при загрузке данных для собеседования: ' + e.message);
        window.location.href = 'index.html';
        return;
    }
    
    // Текущий индекс вопроса
    let currentIndex = 0;
    
    // Функция для обновления прогресса
    function updateProgress() {
        const progress = ((currentIndex + 1) / questions.length) * 100;
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `Вопрос ${currentIndex + 1} из ${questions.length}`;
    }
    
    // Функция для отображения текущего вопроса
    function showCurrentQuestion() {
        const current = questions[currentIndex];
        
        if (!current) {
            console.error('Вопрос не найден для индекса', currentIndex);
            return;
        }
        
        // Отображаем информацию о текущем вопросе
        currentTechnology.textContent = current.technology;
        currentQuestion.textContent = `${current.questionNumber}. ${current.question}`;
        answerInput.value = current.answer || '';
        answerInput.focus();
        
        // Обновляем состояние кнопок
        prevQuestionBtn.disabled = currentIndex === 0;
        
        if (currentIndex === questions.length - 1) {
            nextQuestionBtn.classList.add('hidden');
            finishInterviewBtn.classList.remove('hidden');
        } else {
            nextQuestionBtn.classList.remove('hidden');
            finishInterviewBtn.classList.add('hidden');
        }
        
        updateProgress();
    }
    
    // Функция для сохранения текущего ответа
    function saveCurrentAnswer() {
        if (currentIndex >= 0 && currentIndex < questions.length) {
            questions[currentIndex].answer = answerInput.value;
            localStorage.setItem('interviewData', JSON.stringify(questions));
        }
    }
    
    // Обработчики событий для кнопок
    prevQuestionBtn.addEventListener('click', function() {
        // Сохраняем текущий ответ
        saveCurrentAnswer();
        
        // Переходим к предыдущему вопросу
        if (currentIndex > 0) {
            currentIndex--;
            showCurrentQuestion();
        }
    });
    
    nextQuestionBtn.addEventListener('click', function() {
        // Сохраняем текущий ответ
        saveCurrentAnswer();
        
        // Переходим к следующему вопросу
        if (currentIndex < questions.length - 1) {
            currentIndex++;
            showCurrentQuestion();
        }
    });
    
    // Автосохранение ответа при вводе
    answerInput.addEventListener('input', function() {
        // Сохраняем ответ с небольшой задержкой для производительности
        clearTimeout(answerInput.saveTimeout);
        answerInput.saveTimeout = setTimeout(function() {
            saveCurrentAnswer();
        }, 1000);
    });
    
    finishInterviewBtn.addEventListener('click', function() {
        // Сохраняем последний ответ
        saveCurrentAnswer();
        
        // Проверяем, есть ли пустые ответы
        const unansweredQuestions = questions.filter(q => !q.answer || q.answer.trim() === '').length;
        
        if (unansweredQuestions > 0) {
            const confirmFinish = confirm(`У вас остались ${unansweredQuestions} неотвеченных вопросов. Вы уверены, что хотите завершить собеседование?`);
            if (!confirmFinish) {
                return;
            }
        }
        
        // Показываем результаты
        showResults();
    });
    
    // Обработчик нажатия клавиш для навигации
    document.addEventListener('keydown', function(e) {
        // Ctrl+Enter или Cmd+Enter для перехода к следующему вопросу
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            
            if (currentIndex === questions.length - 1) {
                finishInterviewBtn.click();
            } else {
                nextQuestionBtn.click();
            }
        }
    });
    
    returnToMainBtn.addEventListener('click', function() {
        // Спрашиваем пользователя, хочет ли он вернуться на главную
        const confirmReturn = confirm('Вы уверены, что хотите вернуться на главную страницу? Результаты собеседования будут сохранены.');
        
        if (confirmReturn) {
            window.location.href = 'index.html';
        }
    });
    
    // Функция для отображения результатов
    function showResults() {
        interviewCard.classList.add('hidden');
        interviewResults.classList.remove('hidden');
        
        // Формируем HTML для результатов в виде таблицы
        let resultsHTML = `
            <div class="result-header">
                <div class="result-date">Дата собеседования: ${new Date().toLocaleDateString()}</div>
            </div>
        `;
        
        // Группируем вопросы по технологиям и сортируем по номеру вопроса
        const groupedQuestions = {};
        questions.forEach(q => {
            if (!groupedQuestions[q.technology]) {
                groupedQuestions[q.technology] = [];
            }
            groupedQuestions[q.technology].push(q);
        });
        
        // Сортируем вопросы по номеру внутри каждой технологии
        for (const tech in groupedQuestions) {
            groupedQuestions[tech].sort((a, b) => a.questionNumber - b.questionNumber);
        }
        
        // Считаем статистику
        let totalQuestions = 0;
        let answeredQuestions = 0;
        
        // Создаем таблицу для каждой технологии
        for (const tech in groupedQuestions) {
            resultsHTML += `
                <h3 class="technology-result-header">${tech}</h3>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>№</th>
                            <th>Вопрос</th>
                            <th>Ответ</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            // Добавляем вопросы и ответы для текущей технологии
            groupedQuestions[tech].forEach(q => {
                totalQuestions++;
                if (q.answer && q.answer.trim() !== '') {
                    answeredQuestions++;
                }
                
                resultsHTML += `
                    <tr>
                        <td class="result-number-cell">${q.questionNumber}</td>
                        <td class="result-question-cell">${q.question}</td>
                        <td class="result-answer-cell">
                `;
                
                if (q.answer && q.answer.trim() !== '') {
                    // Отображаем ответ как текст
                    resultsHTML += q.answer;
                } else {
                    resultsHTML += '<em>Ответ не предоставлен</em>';
                }
                
                resultsHTML += `
                        </td>
                    </tr>
                `;
            });
            
            resultsHTML += `
                    </tbody>
                </table>
            `;
        }
        
        // Добавляем статистику
        resultsHTML += `
            <div class="result-stats">
                <div>Всего вопросов: ${totalQuestions}</div>
                <div>Отвечено: ${answeredQuestions} (${Math.round((answeredQuestions / totalQuestions) * 100)}%)</div>
            </div>
        `;
        
        resultsContainer.innerHTML = resultsHTML;
        
        // Прокручиваем страницу вверх
        window.scrollTo(0, 0);
    }
    
    // Показываем первый вопрос при загрузке страницы
    showCurrentQuestion();
});
