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
            if (data.technology_questions) {
                displayTechnologies(data.technology_questions);
            } else if (data.questions_by_technology) {
                displayTechnologies(data.questions_by_technology);
            } else if (data.technologys && Array.isArray(data.technologys)) {
                // Если есть массив технологий, но нет вопросов в нужном формате
                console.log('Найден массив технологий:', data.technologys);
                technologiesList.innerHTML = '<p>Найдены технологии, но вопросы не в ожидаемом формате</p>';
            } else {
                console.error('Отсутствуют поля technology_questions или questions_by_technology в ответе');
                technologiesList.innerHTML = '<p>Технологии не найдены в ответе</p>';
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
                
                // Вариант 1: массив вопросов в поле questions
                if (Array.isArray(tech.questions)) {
                    tech.questions.forEach(q => questions.push(q));
                } 
                // Вариант 2: вопросы в полях question1, question2, ...
                else {
                    for (const key in tech) {
                        if (key.startsWith('question') && typeof tech[key] === 'string') {
                            questions.push(tech[key]);
                        }
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
