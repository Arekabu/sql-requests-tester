// ========== ФУНКЦИИ ЛОГОВ ==========
function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logsDiv = document.getElementById('logs');
    
    if (!logsDiv) return;
    
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

// ========== ПОДКЛЮЧЕНИЕ К БД ==========
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

// ========== ОСНОВНАЯ ФУНКЦИЯ ВЫПОЛНЕНИЯ ==========
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
                if (result.is_multi_select) {
                    addLog(`✅ Запрос ${result.query_num}: ${result.selects_count} SELECT запросов`, 'success');
                } else {
                    addLog(`✅ Запрос ${result.query_num}: успешно (${result.rows_count || 0} строк)`, 'success');
                }
            } else {
                addLog(`❌ Запрос ${result.query_num}: ${result.error}`, 'error');
            }
        }
        
        // Отображаем результаты
        displayResults(data.results);
        
    } catch (error) {
        addLog(`❌ Ошибка выполнения: ${error.message}`, 'error');
        document.getElementById('results').innerHTML = `<div class="error">❌ Ошибка: ${error.message}</div>`;
    }
}

// ========== ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ ==========
function displayResults(results) {
    let html = '<h3>📊 Результаты:</h3>';
    
    for (const result of results) {
        html += '<div class="result">';
        html += `<div class="result-header">📝 Запрос ${result.query_num}</div>`;
        html += '<div class="result-content">';
        
        if (!result.success) {
            html += `<div class="error">❌ ${escapeHtml(result.error)}</div>`;
        }
        else if (result.is_multi_select) {
            html += `<div class="success">✅ ${result.selects_count} SELECT запросов</div>`;
            for (let i = 0; i < result.selects.length; i++) {
                const sel = result.selects[i];
                html += `<div class="sub-query">
                            <div class="sub-query-title">🔍 SELECT #${i+1}</div>`;
                html += renderTable(sel.data);
                html += `</div>`;
            }
        }
        else if (result.data && result.data.length > 0) {
            html += renderTable(result.data);
        }
        else if (result.message) {
            html += `<div class="success">✅ ${escapeHtml(result.message)}</div>`;
        }
        else {
            html += `<div class="success">✅ Выполнено</div>`;
        }

        html += '</div></div>';
    }

    document.getElementById('results').innerHTML = html;
}

function renderTable(data) {
    if (!data || data.length === 0) {
        return '<div class="info">📭 Нет данных</div>';
    }

    const headers = Object.keys(data[0]);
    let table = '<table class="result-table">';
    table += '<thead><tr>' + headers.map(h => `<th>${escapeHtml(h)}</th>`).join('') + '</tr></thead>';
    table += '<tbody>';

    for (const row of data) {
        table += '<tr>';
        for (const h of headers) {
            let value = row[h];
            if (value === null) value = 'NULL';
            if (typeof value === 'object') value = JSON.stringify(value);
            table += `<td>${escapeHtml(String(value))}</td>`;
        }
        table += '</tr>';
    }
    table += '</tbody></table>';
    return table;
}
