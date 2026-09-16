    for url, site_info in data.items():
        # תמיכה בשני הפורמטים (טקסט פשוט או אובייקט עם כותרת)
        if isinstance(site_info, str):
            title = url
            content = site_info
        else:
            title = site_info.get("title", url)
            content = site_info.get("content", "")
            
        content_lower = content.lower()
        
        # בדיקה שכל מילות החיפוש קיימות בדף
        if all(word in content_lower for word in query_words):
            total_matches = sum(content_lower.count(word) for word in query_words)
            
            # תיקון קריטי: לוקחים את המילה הראשונה מתוך הרשימה ומחפשים את המיקום שלה
            first_word = query_words[0] if query_words else ""
            start_idx = content_lower.find(first_word)
            
            if start_idx != -1:
                start = max(0, start_idx - 40)
                end = min(len(content), start_idx + 150)
                snippet = content[start:end]
            else:
                snippet = content[:150]
                
            search_results.append({
                "url": url,
                "title": title,
                "score": total_matches,
                "snippet": snippet
            })
