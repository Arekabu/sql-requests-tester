async function connect() {
    const data = {
        host: document.getElementById('host').value,
        port: document.getElementById('port').value,
        user: document.getElementById('user').value,
        password: document.getElementById('password').value,
        database: document.getElementById('database').value
    };
    const response = await fetch('/connect_db', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    const result = await response.json();
    alert(result.message);
}
async function execute() {
    const response = await fetch('/execute', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query1: document.getElementById('query1').value,
            query2: document.getElementById('query2').value,
            isolation_level: document.getElementById('isolation').value,
            single_transaction: document.getElementById('singleTransaction').checked
        })
    });
    const data = await response.json();
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
}
