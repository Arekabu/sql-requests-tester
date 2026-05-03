function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logsDiv = document.getElementById('logs');

    if (!logsDiv) return; // если блока логов нет на странице

    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `
        <span class="log-time">[${timestamp}]</span>
        <span class="log-${type}">${escapeHtml(message)}</span>
    `;

    logsDiv.appendChild(entry);
    entry.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    while (logsDiv.children.length > 100) {
        logsDiv.removeChild(logsDiv.firstChild);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function clearLogs() {
    const logsDiv = document.getElementById('logs');
    if (logsDiv) {
        logsDiv.innerHTML = '<div class="log-info">⏳ Логи будут появляться здесь...</div>';
    }
    addLog('Логи очищены', 'info');
}

async function connect() {
    const data = {
        host: document.getElementById('host').value,
        port: document.getElementById('port').value,
        user: document.getElementById('user').value,
        password: document.getElementById('password').value,
        database: document.getElementById('database').value
    };

    addLog(`🔌 Подключение к ${data.host}:${data.port}/${data.database}`, 'info');

    try {
        const response = await fetch('/connect_db', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();

        if (result.status === 'success') {
            addLog(`✅ ${result.message}`, 'success');
        } else {
            addLog(`❌ ${result.message}`, 'error');
        }
        alert(result.message);
    } catch (error) {
        addLog(`❌ Ошибка подключения: ${error.message}`, 'error');
        alert('Ошибка: ' + error.message);
    }
}

async function execute() {
    const query1 = document.getElementById('query1').value;
    const query2 = document.getElementById('query2').value;
    const isolation = document.getElementById('isolation').value;

    if (!query1.trim() || !query2.trim()) {
        addLog('⚠️ Введите оба запроса', 'error');
        alert('Введите оба запроса');
        return;
    }

    addLog(`🚀 Запуск запросов (${isolation})`, 'info');
    addLog(`📝 Запрос 1: ${query1.substring(0, 80)}${query1.length > 80 ? '...' : ''}`, 'query');
    addLog(`📝 Запрос 2: ${query2.substring(0, 80)}${query2.length > 80 ? '...' : ''}`, 'query');

    const startTime = Date.now();

    try {
        const response = await fetch('/execute', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query1: query1,
                query2: query2,
                isolation_level: isolation
            })
        });

        const duration = Date.now() - startTime;
        addLog(`📡 Ответ получен за ${duration}мс`, 'success');

        const data = await response.json();

        // Логируем результаты
        for (const result of data.results) {
            if (result.success) {
                addLog(`✅ Запрос ${result.query_num}: успешно (${result.rows_count} строк)`, 'success');
            } else {
                addLog(`❌ Запрос ${result.query_num}: ${result.error}`, 'error');
            }
        }

        let html = '<h3>Результаты:</h3>';
        for (const result of data.results) {
            html += '<div class="result">';
            html += '<b>Запрос ' + result.query_num + '</b><br>';
            if (result.success) {
                html += '<span class="success">✓ Успешно</span><br>';
                if (result.data && result.data.length > 0) {
                    html += '<table>';
                    const headers = Object.keys(result.data[0]);
                    html += '<tr>';
                    for (const h of headers) html += '<th>' + h + '</th>';
                    html += '</tr>';
                    for (const row of result.data) {
                        html += '<tr>';
                        for (const v of Object.values(row)) {
                            html += '<td>' + (v !== null ? v : 'NULL') + '</td>';
                        }
                        html += '</tr>';
                    }
                    html += '</table>';
                }
            } else {
                html += '<span class="error">✗ Ошибка: ' + result.error + '</span>';
            }
            html += '</div>';
        }
        document.getElementById('results').innerHTML = html;

    } catch (error) {
        addLog(`❌ Ошибка выполнения: ${error.message}`, 'error');
        document.getElementById('results').innerHTML = `<div class="error">❌ Ошибка: ${error.message}</div>`;
    }
}
