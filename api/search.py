<!-- החלף רק את חלק ה-JavaScript בתוך קובץ ה-HTML שלך, או את כולו -->
<script>
    function updateStatusLoop() {
        fetch('/api/status')
            .then(res => res.json())
            .then(data => {
                document.getElementById('status-text').innerText = `האינפיניטי סרק עד כה ${data.total_crawled} אתרים זמינים בענן.`;
            })
            .catch(() => {});
        setTimeout(updateStatusLoop, 3000);
    }
    updateStatusLoop();

    document.getElementById('search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') triggerSearch();
    });

    function escapeAndHighlight(text, query) {
        let dummy = document.createElement('div');
        dummy.textContent = text;
        let safeText = dummy.innerHTML;

        if (!query) return safeText;
        const words = query.split(/\s+/).filter(w => w.length > 0);
        
        words.forEach(word => {
            const safeWord = word.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
            const regex = new RegExp(`(${safeWord})`, 'gi');
            safeText = safeText.replace(regex, '<span class="highlight">$1</span>');
        });
        
        return safeText;
    }

    function triggerSearch() {
        const query = document.getElementById('search-input').value.trim();
        if (!query) return;

        const container = document.getElementById('results-container');
        container.innerHTML = '<div class="no-results">מנתח נתונים מוצפנים...</div>';

        fetch(`/api/search?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                container.innerHTML = '';
                
                if (data.results.length === 0) {
                    container.innerHTML = '<div class="no-results">🏜️ סופת החול לא מצאה התאמות לביטוי המבוקש.</div>';
                    return;
                }

                data.results.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'result-item';
                    
                    // אבטחה והדגשה לכותרת ולתקציר הטקסט
                    const secureTitle = escapeAndHighlight(item.title, query);
                    const secureSnippet = escapeAndHighlight(item.snippet, query);

                    // הצגת כותרת האתר כלינק ראשי, וכתובת ה-URL מתחתיה בגוון אדמה קטן
                    div.innerHTML = `
                        <a class="result-url" href="${item.url}" target="_blank" rel="noopener noreferrer">${secureTitle}</a>
                        <div class="result-meta" style="font-size: 0.8rem; color: #8c7355; margin-top: 2px;">🔗 ${item.url} • מופעים בדף: <strong>${item.score}</strong></div>
                        <div class="result-snippet" style="margin-top: 6px;">${secureSnippet}</div>
                    `;
                    container.appendChild(div);
                });
            });
    }
</script>
