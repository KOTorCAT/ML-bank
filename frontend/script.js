document.addEventListener('DOMContentLoaded', () => {
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
    const sendRecordsBtn = document.getElementById('sendRecordsBtn');
    const manualJsonResult = document.getElementById('manualJsonResult');

    // CSV предсказание
    const csvFileInput = document.getElementById('csvFileInput');
    const predictCsvBtn = document.getElementById('predictCsvBtn');
    const csvResult = document.getElementById('csvResult');

    let records = [];

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
        const requiredFields = [
            'person_age', 'person_income', 'person_emp_exp', 'loan_amnt',
            'loan_int_rate', 'loan_percent_income', 'cb_person_cred_hist_length', 'credit_score'
        ];

        for (const field of requiredFields) {
            if (data[field] === 0 || isNaN(data[field])) {
                alert('Пожалуйста, заполните поле "' + field + '"');
                return;
            }
        }

        records.push(data);
        updateDisplay();
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

    // Обновить таблицу
    function updateDisplay() {
        if (records.length === 0) {
            recordsTableContainer.innerHTML = '<p style="padding: 16px; text-align: center; color: #94a3b8;">Нет добавленных записей</p>';
            recordsCount.textContent = '0';
            return;
        }

        recordsCount.textContent = records.length;

        let html = '<table><thead><tr>' +
            '<th>#</th><th>Возраст</th><th>Пол</th><th>Образование</th>' +
            '<th>Доход</th><th>Стаж</th><th>Жилье</th><th>Сумма</th>' +
            '<th>Цель</th><th>Ставка</th><th>Отношение</th><th>Ист.</th>' +
            '<th>Скоринг</th><th>Дефолт</th><th></th>' +
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
    }

    // Отправить записи на предсказание
    async function sendRecords() {
        if (records.length === 0) {
            manualJsonResult.innerHTML = '<pre class="error">Нет записей для отправки</pre>';
            return;
        }

        sendRecordsBtn.disabled = true;
        manualJsonResult.innerHTML = '<pre class="success">Отправка запроса...</pre>';

        try {
            const response = await fetch('/model/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ records: records })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Ошибка ' + response.status);

            manualJsonResult.innerHTML = '';
            const results = data.records || [];

            const header = document.createElement('div');
            header.style.cssText = 'font-weight:600;margin-bottom:12px;font-size:0.95rem;';
            header.textContent = 'Результаты (' + results.length + ' записей)';
            manualJsonResult.appendChild(header);

            results.forEach((result, i) => {
                const isApproved = result.loan_status === 1;
                const div = document.createElement('div');
                div.className = 'prediction-result ' + (isApproved ? 'approved' : 'rejected');
                div.innerHTML =
                    '<span class="status-icon">' + (isApproved ? 'Одобрено' : 'Отказ') + '</span>' +
                    '<span class="status-text">Запись #' + (i + 1) + ': ' + result.loan_status_label + '</span>' +
                    '<span class="probability">Вероятность: ' + (result.probability ? (result.probability * 100).toFixed(1) + '%' : '—') + '</span>';
                manualJsonResult.appendChild(div);
            });
        } catch (error) {
            manualJsonResult.innerHTML = '<pre class="error">Ошибка: ' + error.message + '</pre>';
        } finally {
            sendRecordsBtn.disabled = false;
        }
    }

    // Проверка статуса
    async function checkHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            statusDot.className = 'status-dot';
            if (data.model_loaded) {
                statusDot.classList.add('success');
                statusText.textContent = 'Модель загружена';
            } else {
                statusText.textContent = 'Модель не загружена';
            }
        } catch (error) {
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Сервер недоступен';
        }
    }

    // CSV предсказание
    async function predictCsv() {
        const file = csvFileInput.files[0];
        if (!file) {
            csvResult.innerHTML = '<pre class="error">Выберите CSV-файл</pre>';
            return;
        }

        predictCsvBtn.disabled = true;
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
            info.textContent = 'Обработано: ' + data.rows_processed + ' строк' +
                (data.roc_auc !== null ? '\nROC-AUC: ' + parseFloat(data.roc_auc).toFixed(4) : '');
            csvResult.appendChild(info);

            if (data.csv_data) {
                const rows = data.csv_data.trim().split('\n');
                if (rows.length > 1) {
                    const table = document.createElement('table');
                    const thead = document.createElement('thead');
                    const trHead = document.createElement('tr');
                    rows[0].split(',').forEach(h => {
                        const th = document.createElement('th');
                        th.textContent = h.trim();
                        trHead.appendChild(th);
                    });
                    thead.appendChild(trHead);
                    table.appendChild(thead);

                    const tbody = document.createElement('tbody');
                    for (let i = 1; i < Math.min(rows.length, 51); i++) {
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
                }
            }
        } catch (error) {
            csvResult.innerHTML = '<pre class="error">Ошибка: ' + error.message + '</pre>';
        } finally {
            predictCsvBtn.disabled = false;
            csvFileInput.value = '';
        }
    }

    window.removeRecord = removeRecord;

    addRecordBtn.addEventListener('click', addRecord);
    clearRecordsBtn.addEventListener('click', clearRecords);
    sendRecordsBtn.addEventListener('click', sendRecords);
    predictCsvBtn.addEventListener('click', predictCsv);

    updateDisplay();
    checkHealth();
    setInterval(checkHealth, 15000);
});