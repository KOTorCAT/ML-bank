document.addEventListener('DOMContentLoaded', () => {
    // --- DOM элементы ---
    // Статус
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    // Форма ручного ввода
    const person_age = document.getElementById('person_age');
    const person_gender = document.getElementById('person_gender');
    const person_education = document.getElementById('person_education');
    const person_income = document.getElementById('person_income');
    const person_emp_exp = document.getElementById('person_emp_exp');
    const person_home_ownership = document.getElementById('person_home_ownership');
    const loan_amnt = document.getElementById('loan_amnt');
    const loan_intent = document.getElementById('loan_intent');
    const loan_int_rate = document.getElementById('loan_int_rate');
    const loan_percent_income = document.getElementById('loan_percent_income');
    const cb_person_cred_hist_length = document.getElementById('cb_person_cred_hist_length');
    const credit_score = document.getElementById('credit_score');
    const previous_loan_defaults_on_file = document.getElementById('previous_loan_defaults_on_file');

    const addRecordBtn = document.getElementById('addRecordBtn');
    const clearRecordsBtn = document.getElementById('clearRecordsBtn');
    const recordsTableContainer = document.getElementById('recordsTableContainer');
    const recordsCount = document.getElementById('recordsCount');
    const jsonPreview = document.getElementById('jsonPreview');
    const csvPreview = document.getElementById('csvPreview');
    const previewContainer = document.getElementById('previewContainer');
    const sendRecordsBtn = document.getElementById('sendRecordsBtn');
    const manualJsonResult = document.getElementById('manualJsonResult');

    // CSV предсказание
    const csvFileInput = document.getElementById('csvFileInput');
    const predictCsvBtn = document.getElementById('predictCsvBtn');
    const csvResult = document.getElementById('csvResult');

    // Статистика
    const getStatsBtn = document.getElementById('getStatsBtn');
    const statsResult = document.getElementById('statsResult');

    // --- Проверка существования элементов ---
    console.log('csvFileInput:', csvFileInput);
    console.log('predictCsvBtn:', predictCsvBtn);
    console.log('csvResult:', csvResult);

    // --- Состояние ---
    let records = [];

    // --- Функции ---

    // Получить данные из формы
    function getFormData() {
        return {
            person_age: parseFloat(person_age.value) || 0,
            person_gender: parseInt(person_gender.value) || 0,
            person_education: parseInt(person_education.value) || 0,
            person_income: parseFloat(person_income.value) || 0,
            person_emp_exp: parseInt(person_emp_exp.value) || 0,
            person_home_ownership: parseInt(person_home_ownership.value) || 0,
            loan_amnt: parseFloat(loan_amnt.value) || 0,
            loan_intent: parseInt(loan_intent.value) || 0,
            loan_int_rate: parseFloat(loan_int_rate.value) || 0,
            loan_percent_income: parseFloat(loan_percent_income.value) || 0,
            cb_person_cred_hist_length: parseFloat(cb_person_cred_hist_length.value) || 0,
            credit_score: parseInt(credit_score.value) || 0,
            previous_loan_defaults_on_file: parseInt(previous_loan_defaults_on_file.value) || 0
        };
    }

    // Добавить запись
    function addRecord() {
        const data = getFormData();

        // Поля, которые могут иметь значение 0 (это валидные значения для select)
        const fieldsThatCanBeZero = [
            'person_gender',
            'person_education',
            'person_home_ownership',
            'loan_intent',
            'previous_loan_defaults_on_file'
        ];

        // Поля, которые должны быть больше 0
        const requiredFields = [
            'person_age',
            'person_income',
            'person_emp_exp',
            'loan_amnt',
            'loan_int_rate',
            'loan_percent_income',
            'cb_person_cred_hist_length',
            'credit_score'
        ];

        // Проверяем обязательные поля (должны быть > 0)
        for (const field of requiredFields) {
            const value = data[field];
            if (value === 0 || value === null || value === undefined || isNaN(value)) {
                alert('Пожалуйста, заполните поле "' + field + '" корректным значением (не 0).');
                return;
            }
            // Дополнительная проверка для возраста
            if (field === 'person_age' && (value < 18 || value > 100)) {
                alert('Возраст должен быть от 18 до 100 лет.');
                return;
            }
            // Проверка для кредитного скоринга
            if (field === 'credit_score' && (value < 300 || value > 850)) {
                alert('Кредитный скоринг должен быть от 300 до 850.');
                return;
            }
        }

        // Проверяем, что все select поля имеют валидные значения (не NaN)
        for (const field of fieldsThatCanBeZero) {
            const value = data[field];
            if (isNaN(value) || value === null || value === undefined) {
                alert('Пожалуйста, выберите значение для поля "' + field + '".');
                return;
            }
        }

        records.push(data);
        updateDisplay();

        // Очищаем результат предсказания при добавлении новой записи
        manualJsonResult.innerHTML = '';
    }

    // Удалить запись
    function removeRecord(index) {
        records.splice(index, 1);
        updateDisplay();
        manualJsonResult.innerHTML = '';
    }

    // Очистить все
    function clearRecords() {
        if (records.length === 0) return;
        if (confirm('Удалить все записи?')) {
            records = [];
            updateDisplay();
            manualJsonResult.innerHTML = '';
        }
    }

    // Обновить отображение (таблица + скрытые JSON и CSV)
    function updateDisplay() {
        // Обновить таблицу
        if (records.length === 0) {
            recordsTableContainer.innerHTML = '<p style="padding: 16px; text-align: center; color: #94a3b8;">Нет добавленных записей</p>';
            recordsCount.textContent = '0';
            // Очищаем JSON и CSV превью
            if (jsonPreview) jsonPreview.textContent = '';
            if (csvPreview) csvPreview.textContent = '';
            return;
        }

        recordsCount.textContent = records.length;

        // Таблица
        let html = '<table><thead><tr>' +
            '<th>#</th><th>Возраст</th><th>Пол</th><th>Образование</th>' +
            '<th>Доход</th><th>Стаж</th><th>Жилье</th><th>Сумма</th>' +
            '<th>Цель</th><th>Ставка</th><th>Отношение</th><th>Ист.</th>' +
            '<th>Скоринг</th><th>Дефолт</th><th>Действия</th>' +
            '</tr></thead><tbody>';

        records.forEach((record, i) => {
            html += '<tr>' +
                '<td>' + (i + 1) + '</td>' +
                '<td>' + record.person_age + '</td>' +
                '<td>' + record.person_gender + '</td>' +
                '<td>' + record.person_education + '</td>' +
                '<td>' + record.person_income + '</td>' +
                '<td>' + record.person_emp_exp + '</td>' +
                '<td>' + record.person_home_ownership + '</td>' +
                '<td>' + record.loan_amnt + '</td>' +
                '<td>' + record.loan_intent + '</td>' +
                '<td>' + record.loan_int_rate + '</td>' +
                '<td>' + record.loan_percent_income + '</td>' +
                '<td>' + record.cb_person_cred_hist_length + '</td>' +
                '<td>' + record.credit_score + '</td>' +
                '<td>' + record.previous_loan_defaults_on_file + '</td>' +
                '<td><button class="btn-small btn-danger-small" onclick="window.removeRecord(' + i + ')">X</button></td>' +
                '</tr>';
        });

        html += '</tbody></table>';
        recordsTableContainer.innerHTML = html;

        // Обновляем JSON и CSV превью (скрытые)
        if (jsonPreview) {
            const jsonData = { records: records };
            jsonPreview.textContent = JSON.stringify(jsonData, null, 2);
        }

        if (csvPreview) {
            if (records.length > 0) {
                const headers = Object.keys(records[0]);
                let csv = headers.join(',') + '\n';
                records.forEach(record => {
                    csv += headers.map(h => record[h]).join(',') + '\n';
                });
                csvPreview.textContent = csv;
            } else {
                csvPreview.textContent = 'Нет данных';
            }
        }
    }

    // Показать/скрыть JSON и CSV превью (для разработчика)
    function togglePreview() {
        if (previewContainer) {
            if (previewContainer.style.display === 'none') {
                previewContainer.style.display = 'grid';
            } else {
                previewContainer.style.display = 'none';
            }
        }
    }

    // Отправить все записи на предсказание
    async function sendRecords() {
        if (records.length === 0) {
            showResult(manualJsonResult, 'Нет записей для отправки. Добавьте хотя бы одну.', true);
            return;
        }

        const jsonData = { records: records };
        sendRecordsBtn.disabled = true;
        showLoading(manualJsonResult, 'Отправка запроса...');

        try {
            const response = await fetch('/model/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(jsonData)
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Ошибка ' + response.status);

            manualJsonResult.innerHTML = '';
            const results = data.records || [];

            const header = document.createElement('div');
            header.style.cssText = 'font-weight:600;margin-bottom:12px;font-size:0.95rem;';
            header.textContent = 'Результаты предсказания (' + results.length + ' записей)';
            manualJsonResult.appendChild(header);

            results.forEach((result, i) => {
                const isApproved = result.loan_status === 1;
                const div = document.createElement('div');
                div.className = 'prediction-result ' + (isApproved ? 'approved' : 'rejected');
                div.innerHTML =
                    '<span class="status-icon">' + (isApproved ? 'Одобрено' : 'Отказ') + '</span>' +
                    '<span class="status-text">Запись #' + (i + 1) + ': ' + (result.loan_status_label || (isApproved ? 'Одобрено' : 'Отказ')) + '</span>' +
                    '<span class="probability">Вероятность: ' + (result.probability ? (result.probability * 100).toFixed(1) + '%' : '—') + '</span>';
                manualJsonResult.appendChild(div);
            });

            const details = document.createElement('details');
            details.style.cssText = 'margin-top:12px;';
            const summary = document.createElement('summary');
            summary.style.cssText = 'cursor:pointer;font-size:0.85rem;color:#64748b;';
            summary.textContent = 'Показать полный ответ';
            details.appendChild(summary);
            const pre = document.createElement('pre');
            pre.style.cssText = 'font-size:0.75rem;max-height:200px;overflow-y:auto;margin-top:8px;';
            pre.textContent = JSON.stringify(data, null, 2);
            details.appendChild(pre);
            manualJsonResult.appendChild(details);

        } catch (error) {
            showResult(manualJsonResult, error.message, true);
        } finally {
            sendRecordsBtn.disabled = false;
        }
    }

    // --- UI функции ---
    function setStatus(state, message) {
        if (!statusDot || !statusText) return;
        statusDot.className = 'status-dot';
        if (state === 'loading') statusDot.classList.add('loading');
        else if (state === 'success') statusDot.classList.add('success');
        else if (state === 'error') statusDot.classList.add('error');
        statusText.textContent = message;
    }

    function showResult(element, data, isError = false) {
        if (!element) return;
        element.innerHTML = '';
        const pre = document.createElement('pre');
        if (isError) {
            pre.className = 'error';
            pre.textContent = 'Ошибка: ' + data;
        } else {
            pre.className = 'success';
            if (typeof data === 'object') {
                pre.textContent = JSON.stringify(data, null, 2);
            } else {
                pre.textContent = data;
            }
        }
        element.appendChild(pre);
    }

    function showLoading(element, message) {
        if (!element) return;
        element.innerHTML = '<pre class="success">' + message + '</pre>';
    }

    // --- Проверка статуса ---
    async function checkHealth() {
        setStatus('loading', 'Проверка...');
        try {
            const response = await fetch('/health');
            if (!response.ok) throw new Error('HTTP ' + response.status);
            const data = await response.json();
            if (data.model_loaded) {
                setStatus('success', 'Модель загружена');
            } else {
                setStatus('default', 'Модель не загружена');
            }
        } catch (error) {
            setStatus('error', 'Сервер недоступен');
            console.error('Health check error:', error);
        }
    }

    // --- CSV предсказание ---
    async function predictCsv() {
        console.log('predictCsv function called');
        
        if (!csvFileInput || !csvResult) {
            console.error('CSV elements not found');
            return;
        }
        
        const file = csvFileInput.files[0];
        if (!file) {
            showResult(csvResult, 'Выберите CSV-файл', true);
            return;
        }
        if (!file.name.endsWith('.csv')) {
            showResult(csvResult, 'Неверный формат. Ожидается .csv', true);
            return;
        }

        if (predictCsvBtn) predictCsvBtn.disabled = true;
        csvResult.innerHTML = '<pre class="success">Обработка CSV...</pre>';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/model/predict-from-csv', { method: 'POST', body: formData });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Ошибка ' + response.status);

            csvResult.innerHTML = '';
            const info = document.createElement('pre');
            info.className = 'success';
            let infoText = 'Обработано: ' + data.rows_processed + ' строк';
            if (data.roc_auc !== null && data.roc_auc !== undefined) {
                infoText += '\nROC-AUC: ' + parseFloat(data.roc_auc).toFixed(4);
            }
            info.textContent = infoText;
            csvResult.appendChild(info);

            if (data.csv_data) {
                const rows = data.csv_data.trim().split('\n');
                if (rows.length > 1) {
                    const table = document.createElement('table');
                    const thead = document.createElement('thead');
                    const headers = rows[0].split(',');
                    const trHead = document.createElement('tr');
                    headers.forEach(h => {
                        const th = document.createElement('th');
                        th.textContent = h.trim();
                        trHead.appendChild(th);
                    });
                    thead.appendChild(trHead);
                    table.appendChild(thead);

                    const tbody = document.createElement('tbody');
                    const maxRows = Math.min(rows.length - 1, 50);
                    for (let i = 1; i <= maxRows; i++) {
                        const tr = document.createElement('tr');
                        rows[i].split(',').forEach(cell => {
                            const td = document.createElement('td');
                            td.textContent = cell.trim();
                            tr.appendChild(td);
                        });
                        tbody.appendChild(tr);
                    }
                    table.appendChild(tbody);
                    csvResult.appendChild(table);

                    if (rows.length - 1 > 50) {
                        const note = document.createElement('p');
                        note.textContent = '... и еще ' + (rows.length - 1 - 50) + ' строк';
                        note.style.cssText = 'font-size:0.8rem;color:#64748b;margin-top:8px;';
                        csvResult.appendChild(note);
                    }
                }
            }
        } catch (error) {
            csvResult.innerHTML = '<pre class="error">Ошибка: ' + error.message + '</pre>';
        } finally {
            if (predictCsvBtn) predictCsvBtn.disabled = false;
            if (csvFileInput) csvFileInput.value = '';
        }
    }

    // --- Статистика ---
    async function getStats() {
        if (!getStatsBtn) return;
        getStatsBtn.disabled = true;
        if (statsResult) showLoading(statsResult, 'Загрузка статистики...');

        try {
            const response = await fetch('/model/stats');
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Ошибка ' + response.status);

            if (!statsResult) return;
            
            const stats = data.data;

            // Статистика в карточках
            let html = '<div class="stats-grid">' +
                '<div class="stat-item models">' +
                    '<span class="stat-number">' + stats.models_uploaded + '</span>' +
                    '<span class="stat-label">Моделей</span>' +
                '</div>' +
                '<div class="stat-item predictions">' +
                    '<span class="stat-number">' + stats.predictions_made + '</span>' +
                    '<span class="stat-label">Предсказаний</span>' +
                '</div>' +
                '<div class="stat-item approved">' +
                    '<span class="stat-number">' + stats.approved + '</span>' +
                    '<span class="stat-label">Одобрено</span>' +
                '</div>' +
                '<div class="stat-item rejected">' +
                    '<span class="stat-number">' + stats.rejected + '</span>' +
                    '<span class="stat-label">Отказов</span>' +
                '</div>' +
            '</div>';

            // Последние 10 запросов в виде красивой таблицы
            if (stats.recent_predictions && stats.recent_predictions.length > 0) {
                html += '<div style="margin-top: 20px;">' +
                    '<h4 style="font-weight: 600; font-size: 0.95rem; margin-bottom: 12px;">Последние 10 запросов</h4>' +
                    '<div style="overflow-x: auto; border-radius: 8px; border: 1px solid #e2e8f0;">' +
                    '<table style="width: 100%; border-collapse: collapse; font-size: 0.75rem;">' +
                    '<thead style="background: #f1f5f9;">' +
                    '<tr>' +
                    '<th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">#</th>' +
                    '<th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Статус</th>' +
                    '<th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Вероятность</th>' +
                    '<th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Источник</th>' +
                    '<th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата</th>' +
                    '</tr>' +
                    '</thead><tbody>';

                stats.recent_predictions.forEach((item, index) => {
                    const isApproved = item.prediction === 1;
                    const statusLabel = isApproved ? 'Одобрено' : 'Отказ';
                    const statusColor = isApproved ? '#22c55e' : '#ef4444';
                    const bgColor = isApproved ? '#dcfce7' : '#fee2e2';

                    let dateStr = item.created_at || '—';
                    try {
                        const date = new Date(dateStr);
                        if (!isNaN(date.getTime())) {
                            dateStr = date.toLocaleString('ru-RU', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                        }
                    } catch (e) {}

                    let prob = item.probability;
                    if (prob !== null && prob !== undefined) {
                        prob = (parseFloat(prob) * 100).toFixed(1) + '%';
                    } else {
                        prob = '—';
                    }

                    html += '<tr style="border-bottom: 1px solid #f1f5f9;">' +
                        '<td style="padding: 8px 12px;">' + (index + 1) + '</td>' +
                        '<td style="padding: 8px 12px;">' +
                            '<span style="display: inline-block; padding: 2px 12px; border-radius: 12px; background: ' + bgColor + '; color: ' + statusColor + '; font-weight: 600; font-size: 0.7rem;">' +
                                statusLabel +
                            '</span>' +
                        '</td>' +
                        '<td style="padding: 8px 12px; font-weight: 500;">' + prob + '</td>' +
                        '<td style="padding: 8px 12px; color: #64748b;">' + (item.source || '—') + '</td>' +
                        '<td style="padding: 8px 12px; color: #64748b; white-space: nowrap;">' + dateStr + '</td>' +
                        '</tr>';
                });

                html += '</tbody></table></div></div>';
            }

            statsResult.innerHTML = html;

        } catch (error) {
            if (statsResult) statsResult.innerHTML = '<pre class="error">Ошибка: ' + error.message + '</pre>';
        } finally {
            if (getStatsBtn) getStatsBtn.disabled = false;
        }
    }

    // --- Экспорт функций для использования в onclick ---
    window.removeRecord = removeRecord;
    window.addRecord = addRecord;
    window.togglePreview = togglePreview;

    // --- Навешиваем события ---
    if (addRecordBtn) addRecordBtn.addEventListener('click', addRecord);
    if (clearRecordsBtn) clearRecordsBtn.addEventListener('click', clearRecords);
    if (sendRecordsBtn) sendRecordsBtn.addEventListener('click', sendRecords);

    if (predictCsvBtn) {
        console.log('Adding click event to predictCsvBtn');
        predictCsvBtn.addEventListener('click', predictCsv);
    } else {
        console.error('predictCsvBtn not found');
    }
    
    if (getStatsBtn) getStatsBtn.addEventListener('click', getStats);

    // Enter в полях формы для быстрого добавления
    document.querySelectorAll('.form-group input, .form-group select').forEach(el => {
        el.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addRecord();
            }
        });
    });

    // --- Инициализация ---
    updateDisplay();
    checkHealth();
    setInterval(checkHealth, 15000);

    // Для отладки: показать JSON и CSV по двойному клику на заголовке
    const inputSectionTitle = document.querySelector('#inputSection h2');
    if (inputSectionTitle) {
        inputSectionTitle.addEventListener('dblclick', togglePreview);
    }
});