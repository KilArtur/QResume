// Функция для подготовки данных к формату собеседования
function prepareInterviewData(data) {
    const questions = [];
    
    if (Array.isArray(data)) {
        // Формат массива объектов с технологиями
        data.forEach(tech => {
            const technology = tech.technology || tech.name_technology || 'Неизвестная технология';
            
            if (Array.isArray(tech.questions)) {
                tech.questions.forEach(q => {
                    questions.push({
                        technology: technology,
                        question: q,
                        answer: ''
                    });
                });
            } else {
                // Ищем вопросы в формате question1, question2...
                for (let i = 1; i <= 5; i++) {
                    const key = `question${i}`;
                    if (tech[key] && typeof tech[key] === 'string') {
                        questions.push({
                            technology: technology,
                            question: tech[key],
                            answer: ''
                        });
                    }
                }
            }
        });
    } else if (typeof data === 'object') {
        // Формат объекта, где ключи - названия технологий
        for (const tech in data) {
            if (Array.isArray(data[tech])) {
                // Ограничиваем до 5 вопросов на технологию
                const techQuestions = data[tech].slice(0, 5);
                techQuestions.forEach(q => {
                    questions.push({
                        technology: tech,
                        question: q,
                        answer: ''
                    });
                });
            }
        }
    }
    
    return questions;
}

document.addEventListener('DOMContentLoaded', function() {
    const resumeForm = document.getElementById('resumeForm');
    const resumeFile = document.getElementById('resumeFile');
    const fileName = document.getElementById('fileName');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    const welcomeSection = document.querySelector('.welcome');
    const backButton = document.getElementById('backButton');
    const candidateDetails = document.getElementById('candidateDetails');
    const technologiesList = document.getElementById('technologiesList');
    const startInterviewButton = document.getElementById('startInterviewButton');
    
    // Глобальная переменная для хранения данных резюме
    window.resumeData = null;
    
    // Деактивируем кнопку собеседования до загрузки данных
    if (startInterviewButton) {
        startInterviewButton.disabled = true;
    }
    
    // Обработчик для кнопки "Начать собеседование"
    if (startInterviewButton) {
        startInterviewButton.addEventListener('click', function() {
            if (!window.resumeData) {
                alert('Сначала загрузите резюме');
                return;
            }
            
            // Сохраняем данные для собеседования в localStorage
            let interviewData = [];
            const data = window.resumeData;
            
            try {
                console.log('Данные резюме:', data);
                
                // Извлекаем вопросы из данных резюме
                interviewData = [];
                
                if (data.questions_by_technology && Array.isArray(data.questions_by_technology)) {
                    console.log('Найдены вопросы в формате questions_by_technology');
                    
                    // Обрабатываем вопросы из questions_by_technology (формат из модели CandidateProfile)
                    data.questions_by_technology.forEach(tech => {
                        const technology = tech.name_technology || 'Неизвестная технология';
                        
                        // Собираем вопросы из полей question1, question2, ...
                        for (let i = 1; i <= 5; i++) {
                            const questionKey = `question${i}`;
                            if (tech[questionKey] && typeof tech[questionKey] === 'string') {
                                interviewData.push({
                                    technology: technology,
                                    question: tech[questionKey],
                                    answer: '',
                                    questionNumber: i
                                });
                            }
                        }
                    });
                    
                    console.log('Извлечено вопросов:', interviewData.length);
                } else {
                    console.error('Не найдены вопросы в формате questions_by_technology');
                    alert('Не удалось найти вопросы для собеседования в результатах анализа резюме');
                    return;
                }
                
                if (interviewData.length === 0) {
                    alert('Не найдены вопросы для собеседования');
                    return;
                }
                
                // Сохраняем данные кандидата для отображения на странице собеседования
                const candidateInfo = {
                    name: data.name || data.full_name || data.candidate_name || 'Кандидат',
                    position: data.position || data.desired_position || data.candidate_position || 'Позиция не указана'
                };
                
                // Сохраняем полные данные анализа резюме
                localStorage.setItem('resumeAnalysisData', JSON.stringify(data));
                
                try {
                    // Полностью очищаем localStorage перед сохранением новых данных
                    localStorage.clear();
                    
                    // Сохраняем данные в localStorage
                    localStorage.setItem('candidateInfo', JSON.stringify(candidateInfo));
                    localStorage.setItem('interviewData', JSON.stringify(interviewData));
                    localStorage.setItem('resumeAnalysisData', JSON.stringify(data));
                    
                    console.log('Данные сохранены в localStorage:', 
                                'candidateInfo:', JSON.stringify(candidateInfo),
                                'interviewData:', JSON.stringify(interviewData).substring(0, 100) + '...');
                    
                    // Добавляем задержку перед переходом на страницу собеседования
                    setTimeout(() => {
                        window.location.href = 'interview.html';
                    }, 100);
                } catch (storageError) {
                    console.error('Ошибка при сохранении в localStorage:', storageError);
                    alert('Не удалось сохранить данные для собеседования. Проверьте настройки приватности браузера.');
                }
            } catch (error) {
                console.error('Ошибка при подготовке данных для собеседования:', error);
                alert('Произошла ошибка при подготовке собеседования. Пожалуйста, попробуйте еще раз.');
            }
        });
    }
    
    // Обработка выбора файла
    resumeFile.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            fileName.textContent = this.files[0].name;
        } else {
            fileName.textContent = '';
        }
    });
    
    // Обработка отправки формы
    resumeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!resumeFile.files || !resumeFile.files[0]) {
            alert('Пожалуйста, выберите файл резюме');
            return;
        }
        
        // Показываем индикатор загрузки
        welcomeSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');
        
        const formData = new FormData();
        formData.append('file', resumeFile.files[0]);
        
        // Отправляем запрос на сервер
        fetch('http://localhost:8000/skills', {
            method: 'POST',
            body: formData,
            mode: 'cors'
        })
        .then(response => {
            console.log('Статус ответа:', response.status);
            if (!response.ok) {
                throw new Error(`Ошибка при отправке файла: ${response.status}`);
            }
            return response.json().catch(err => {
                console.error('Ошибка при парсинге JSON:', err);
                throw new Error('Невозможно прочитать ответ как JSON');
            });
        })
        .then(data => {
            console.log('Получены данные:', data);
            
            // Скрываем индикатор загрузки и показываем результаты
            loadingSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            
            // Отображаем информацию о кандидате
            displayCandidateInfo(data);
            
            // Отображаем технологии и вопросы
            if (data.questions_by_technology && Array.isArray(data.questions_by_technology)) {
                displayTechnologies(data.questions_by_technology);
            } else {
                console.error('Отсутствует поле questions_by_technology в ответе');
                technologiesList.innerHTML = '<p>Технологии не найдены в ответе</p>';
            }
            
            // Сохраняем данные в глобальной переменной для доступа из обработчика кнопки
            window.resumeData = data;
            
            // Активируем кнопку "Начать собеседование"
            const startInterviewButton = document.getElementById('startInterviewButton');
            if (startInterviewButton) {
                startInterviewButton.disabled = false;
            }
            
            
        })
        .catch(error => {
            console.error('Ошибка:', error);
            loadingSection.classList.add('hidden');
            welcomeSection.classList.remove('hidden');
            alert('Произошла ошибка при обработке файла. Пожалуйста, попробуйте еще раз.');
        });
    });
    
    // Обработка нажатия кнопки "Вернуться"
    backButton.addEventListener('click', function() {
        resultsSection.classList.add('hidden');
        welcomeSection.classList.remove('hidden');
        resumeFile.value = '';
        fileName.textContent = '';
    });
    
    
    
    // Функция для отображения информации о кандидате
    function displayCandidateInfo(data) {
        candidateDetails.innerHTML = '';
        
        if (!data) {
            candidateDetails.innerHTML = '<p>Данные о кандидате отсутствуют</p>';
            return;
        }
        
        let infoHTML = '';
        
        if (typeof data === 'object') {
            for (const key in data) {
                if (key !== 'technology_questions' && key !== 'questions_by_technology' && key !== 'technologys') {
                    const value = data[key] || 'Не указано';
                    infoHTML += `<p><strong>${key}:</strong> ${value}</p>`;
                }
            }
        } else {
            infoHTML = `<p>${data}</p>`;
        }
        
        if (!infoHTML) {
            infoHTML = '<p>Информация о кандидате отсутствует</p>';
        }
        
        candidateDetails.innerHTML = infoHTML;
    }
    
    // Функция для отображения технологий и вопросов
    function displayTechnologies(technologies) {
        technologiesList.innerHTML = '';
        
        if (!technologies || technologies.length === 0) {
            technologiesList.innerHTML = '<p>Технологии не найдены</p>';
            return;
        }
        
        // Проверяем формат данных
        if (Array.isArray(technologies)) {
            technologies.forEach(tech => {
                const techElement = document.createElement('div');
                techElement.className = 'technology-item';
                
                // Определяем название технологии
                let technologyName = '';
                if (tech.technology) {
                    technologyName = tech.technology;
                } else if (tech.name_technology) {
                    technologyName = tech.name_technology;
                } else {
                    // Если нет явного названия, ищем первое поле, которое может быть названием
                    for (const key in tech) {
                        if (typeof tech[key] === 'string' && !key.startsWith('question')) {
                            technologyName = tech[key];
                            break;
                        }
                    }
                }
                
                const techName = document.createElement('div');
                techName.className = 'technology-name';
                techName.textContent = technologyName;
                
                const questionsList = document.createElement('ul');
                questionsList.className = 'questions-list';
                
                // Собираем вопросы из разных возможных форматов
                const questions = [];
                
                // Вопросы в полях question1, question2, ...
                for (let i = 1; i <= 5; i++) {
                    const key = `question${i}`;
                    if (tech[key] && typeof tech[key] === 'string') {
                        questions.push(tech[key]);
                    }
                }
                
                // Добавляем вопросы в список
                questions.forEach(question => {
                    const questionItem = document.createElement('li');
                    questionItem.className = 'question-item';
                    questionItem.textContent = question;
                    questionsList.appendChild(questionItem);
                });
                
                techElement.appendChild(techName);
                techElement.appendChild(questionsList);
                technologiesList.appendChild(techElement);
            });
        } else if (typeof technologies === 'object') {
            // Если это объект, где ключи - названия технологий, а значения - массивы вопросов
            for (const tech in technologies) {
                const techElement = document.createElement('div');
                techElement.className = 'technology-item';
                
                const techName = document.createElement('div');
                techName.className = 'technology-name';
                techName.textContent = tech;
                
                const questionsList = document.createElement('ul');
                questionsList.className = 'questions-list';
                
                if (Array.isArray(technologies[tech])) {
                    technologies[tech].forEach(question => {
                        const questionItem = document.createElement('li');
                        questionItem.className = 'question-item';
                        questionItem.textContent = question;
                        questionsList.appendChild(questionItem);
                    });
                }
                
                techElement.appendChild(techName);
                techElement.appendChild(questionsList);
                technologiesList.appendChild(techElement);
            }
        }
    }
    
});
